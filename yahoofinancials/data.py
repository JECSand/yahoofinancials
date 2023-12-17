import calendar
import datetime
import logging
import random
import time
from functools import partial
from json import loads
from multiprocessing import Pool
import pytz

from yahoofinancials.maps import COUNTRY_MAP, REQUEST_MAP, USER_AGENTS
from yahoofinancials.sessions import SessionManager, _init_session
from yahoofinancials.utils import remove_prefix, get_request_config, get_request_category

# track the last get timestamp to add a minimum delay between gets - be nice!
_lastget = 0


# Custom Exception class to handle custom error
class ManagedException(Exception):
    pass


# Class used to get data from urls
class UrlOpener:
    request_headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://finance.yahoo.com",
        "referer": "https://finance.yahoo.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }
    user_agent = random.choice(USER_AGENTS)
    request_headers["User-Agent"] = user_agent

    def __init__(self, session):
        self._session_manager = SessionManager(session=session)

    def open(self, url, request_headers=None, params=None, proxy=None, timeout=30):
        response = self._session_manager.cache_get(
            url=url,
            params=params,
            proxy=proxy,
            timeout=timeout,
            user_agent_headers=request_headers or self.request_headers
        )
        return response

    def get_data(self, session, url, request_headers=None, params=None, proxy=None, timeout=30):
        response = session.get(
            url=url,
            params=params,
            proxies=proxy,
            timeout=timeout,
            headers=request_headers or self.request_headers
        )
        return response


class YahooFinanceData(object):

    def __init__(self, ticker, **kwargs):
        self.ticker = ticker.upper() if isinstance(ticker, str) else [t.upper() for t in ticker]
        self.country = kwargs.get("country", "US")
        if self.country.upper() not in COUNTRY_MAP.keys():
            raise ReferenceError("invalid country: " + self.country)
        self.concurrent = kwargs.get("concurrent", False)
        self.max_workers = kwargs.get("max_workers", 8)
        self.timeout = kwargs.get("timeout", 30)
        self.proxies = kwargs.get("proxies")
        self.session = kwargs.pop("session", None)
        self.flat_format = kwargs.get("flat_format", False)
        self._cache = {}

    # Minimum interval between Yahoo Finance requests for this instance
    _MIN_INTERVAL = 7

    # Meta-data dictionaries for the classes to use
    YAHOO_FINANCIAL_TYPES = {
        'income': [
            'income_statement',
            'incomeStatementHistory',
            'incomeStatementHistoryQuarterly',
            'incomeStatements'
        ],
        'balance': [
            'balance_sheet',
            'balanceSheetHistory',
            'balanceSheetHistoryQuarterly',
            'balanceSheetStatements',
        ],
        'cash': [
            'cash_flow',
            'cashflowStatementHistory',
            'cashflowStatementHistoryQuarterly',
            'cashflowStatements',
        ],
        'keystats': ['key-statistics'],
        'history': ['history'],
        'profile': ['summaryProfile']
    }

    # Interval value translation dictionary
    _INTERVAL_DICT = {
        'daily': '1d',
        'weekly': '1wk',
        'monthly': '1mo'
    }

    # Base Yahoo Finance URL for the class to build on
    _BASE_YAHOO_URL = 'https://finance.yahoo.com/quote/'

    # private static method to get the appropriate report type identifier
    @staticmethod
    def get_report_type(frequency):
        if frequency == 'annual':
            report_num = 1
        elif frequency == 'quarterly':
            report_num = 2
        else:
            report_num = 3
        return report_num

    # Public static method to format date serial string to readable format and vice versa
    @staticmethod
    def format_date(in_date):
        if isinstance(in_date, str):
            form_date = int(calendar.timegm(time.strptime(in_date, '%Y-%m-%d')))
        else:
            form_date = str((datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=in_date)).date())
        return form_date

    # Private Static Method to Convert Eastern Time to UTC
    @staticmethod
    def _convert_to_utc(date, mask='%Y-%m-%d %H:%M:%S'):
        utc = pytz.utc
        eastern = pytz.timezone('US/Eastern')
        date_ = datetime.datetime.strptime(date.replace(" 0:", " 12:"), mask)
        date_eastern = eastern.localize(date_, is_dst=None)
        date_utc = date_eastern.astimezone(utc)
        return date_utc.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # _get_proxy randomly picks a proxy in the proxies list if not None
    def _get_proxy(self):
        if self.proxies:
            proxy_str = self.proxies
            if isinstance(self.proxies, list):
                proxy_str = random.choice(self.proxies)
            return {"https": proxy_str}
        return None

    # Private method that determines number of workers to use in a process
    def _get_worker_count(self):
        workers = self.max_workers
        if len(self.ticker) < workers:
            workers = len(self.ticker)
        return workers

    # Private method to construct historical data url
    def _construct_url(self, symbol, config, params, freq, request_type):
        url = config["path"].replace("{symbol}", symbol.lower())
        _default_query_params = COUNTRY_MAP.get(self.country.upper())
        for k, v in config['request'].items():  # request type defaults
            if k == "type":
                params.update({k: v['options'][request_type].get(freq)})
            elif k == "modules" and request_type in v['options']:
                params.update({k: request_type})
            elif k == "symbol":
                params.update({k: symbol.lower()})
            elif k not in params:
                if k == 'reportsCount' and v is None:
                    continue
                params.update({k: v['default']})
        for k, v in _default_query_params.items():  # general defaults
            if k == 'reportsCount' and v is None:
                continue
            if k not in params:
                params.update({k: v})
        if params.get("type"):
            field_params = "%2C".join(params.get("type"))
            url += "?type=" + field_params
            for k, v in params.items():
                if k != "type":
                    url += "&" + k + "=" + str(v)
        elif params.get("modules"):
            url += "?modules=" + params.get("modules")
            for k, v in params.items():
                if k != "modules":
                    url += "&" + k + "=" + str(v)
        elif params.get("symbol"):
            url += "?symbol=" + params.get("symbol")
        return url

    # Private method to execute a web scrape request and decrypt the return
    def _request_handler(self, url, res_field=""):
        urlopener = UrlOpener(self.session)
        # Try to open the URL up to 10 times sleeping random time if something goes wrong
        open_session = False
        cur_url = url
        max_retry = 10
        for i in range(0, max_retry):
            if open_session:
                open_session = False
                try:
                    session, crumb = _init_session(None, proxies=self._get_proxy(), timeout=self.timeout)
                    crumb_url = cur_url + "&crumb=" + str(crumb)
                    response = urlopener.get_data(session, crumb_url, proxy=self._get_proxy(), timeout=self.timeout)
                except:
                    continue
            else:
                try:
                    response = urlopener.open(cur_url, proxy=self._get_proxy(), timeout=self.timeout)
                    if response.status_code == 401:
                        open_session = True
                except AttributeError:
                    open_session = True
                    continue
            if response.status_code != 200:
                time.sleep(random.randrange(1, 5))
                response.close()
                time.sleep(random.randrange(1, 5))
                if response.status_code == 404 and i % 2 == 0:
                    if 'query2.' in cur_url:
                        cur_url = cur_url.replace("query2.", "query1.")
                    elif 'query1.' in cur_url:
                        cur_url = cur_url.replace("query1.", "query2.")

            else:
                res_content = response.text
                response.close()
                self._cache[url] = loads(res_content).get(res_field)
                break
            if i == max_retry - 1:
                # Raise a custom exception if we can't get the web page within max_retry attempts
                raise ManagedException("Server replied with server error code, HTTP " + str(response.status_code) +
                                       " code while opening the url: " + str(cur_url))

    @staticmethod
    def _format_raw_fundamental_data(raw_data):
        data = {}
        for i in raw_data.get("result"):
            for k, v in i.items():
                if k not in ['meta', 'timestamp']:
                    cleaned_k = remove_prefix(remove_prefix(remove_prefix(k, "quarterly"), "annual"), "trailing")
                    if cleaned_k in ['EBIT']:
                        cleaned_k = cleaned_k.lower()
                    else:
                        cleaned_k = cleaned_k[0].lower() + cleaned_k[1:]
                    for rec in v:
                        if rec.get("asOfDate") in data:
                            data[rec.get("asOfDate")].update({cleaned_k: rec.get('reportedValue', {}).get('raw')})
                        else:
                            data.update({rec.get("asOfDate"): {cleaned_k: rec.get('reportedValue', {}).get('raw')}})
        return data

    @staticmethod
    def _format_raw_module_data(raw_data, tech_type):
        data = {}
        for i in raw_data.get("result", {}):
            if i.get(tech_type):
                for k, v in i.get(tech_type, {}).items():
                    data.update({k: v})
        return data

    # Private method to _get_historical_data from yahoo finance
    def _get_historical_data(self, url, config, tech_type, statement_type):
        global _lastget
        if not self._cache.get(url):
            now = int(time.time())
            if _lastget and now - _lastget < self._MIN_INTERVAL:
                time.sleep(self._MIN_INTERVAL - (now - _lastget) + 1)
                now = int(time.time())
            _lastget = now
            self._request_handler(url, config.get("response_field"))
        data = self._cache[url]
        if tech_type == '' and statement_type in ["income", "balance", "cash"]:
            data = self._format_raw_fundamental_data(data)
        elif statement_type == 'analytic':
            data = data.get("result")
            if tech_type == "recommendations":
                if isinstance(data, list) and len(data) > 0:
                    data[0].get("recommendedSymbols")
        else:
            data = self._format_raw_module_data(data, tech_type)
        return data

    # Private static method to determine if a numerical value is in the data object being cleaned
    @staticmethod
    def _determine_numeric_value(value_dict):
        if 'raw' in value_dict.keys():
            numerical_val = value_dict['raw']
        else:
            numerical_val = None
        return numerical_val

    # Private method to format date serial string to readable format and vice versa
    def _format_time(self, in_time):
        form_date_time = datetime.datetime.fromtimestamp(int(in_time)).strftime('%Y-%m-%d %H:%M:%S')
        return self._convert_to_utc(form_date_time)

    # Private method to return a sub dictionary entry for the earning report cleaning
    def _get_cleaned_sub_dict_ent(self, key, val_list):
        sub_list = []
        for rec in val_list:
            sub_sub_dict = {}
            for k, v in rec.items():
                if k == 'date':
                    sub_sub_dict_ent = {k: v}
                else:
                    numerical_val = self._determine_numeric_value(v)
                    sub_sub_dict_ent = {k: numerical_val}
                sub_sub_dict.update(sub_sub_dict_ent)
            sub_list.append(sub_sub_dict)
        return {key: sub_list}

    # Private method to process raw earnings data and clean
    def _clean_earnings_data(self, raw_data):
        cleaned_data = {}
        earnings_key = 'earningsData'
        financials_key = 'financialsData'
        for k, v in raw_data.items():
            if k == 'earningsChart':
                sub_dict = {}
                for k2, v2 in v.items():
                    if k2 == 'quarterly':
                        sub_ent = self._get_cleaned_sub_dict_ent(k2, v2)
                    elif k2 == 'currentQuarterEstimate':
                        numerical_val = self._determine_numeric_value(v2)
                        sub_ent = {k2: numerical_val}
                    else:
                        sub_ent = {k2: v2}
                    sub_dict.update(sub_ent)
                dict_ent = {earnings_key: sub_dict}
                cleaned_data.update(dict_ent)
            elif k == 'financialsChart':
                sub_dict = {}
                for k2, v2, in v.items():
                    sub_ent = self._get_cleaned_sub_dict_ent(k2, v2)
                    sub_dict.update(sub_ent)
                dict_ent = {financials_key: sub_dict}
                cleaned_data.update(dict_ent)
            else:
                if k != 'maxAge':
                    dict_ent = {k: v}
                    cleaned_data.update(dict_ent)
        return cleaned_data

    # Private method to clean summary and price reports
    def _clean_reports(self, raw_data):
        cleaned_dict = {}
        if raw_data is None:
            return None
        for k, v in raw_data.items():
            if 'Time' in k:
                formatted_utc_time = self._format_time(v)
                dict_ent = {k: formatted_utc_time}
            elif 'Date' in k:
                try:
                    formatted_date = v['fmt']
                except (KeyError, TypeError):
                    formatted_date = '-'
                dict_ent = {k: formatted_date}
            elif v is None or isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
                dict_ent = {k: v}
            else:
                numerical_val = self._determine_numeric_value(v)
                dict_ent = {k: numerical_val}
            cleaned_dict.update(dict_ent)
        return cleaned_dict

    # Private Static Method to ensure ticker is URL encoded
    @staticmethod
    def _encode_ticker(ticker_str):
        encoded_ticker = ticker_str.replace('=', '%3D')
        return encoded_ticker

    # Private Method to clean the dates of the newly returns historical stock data into readable format
    def _clean_historical_data(self, hist_data, last_attempt=False):
        data = {}
        for k, v in hist_data.items():
            if k == 'eventsData':
                event_obj = {}
                if isinstance(v, list):
                    dict_ent = {k: event_obj}
                else:
                    for type_key, type_obj in v.items():
                        formatted_type_obj = {}
                        for date_key, date_obj in type_obj.items():
                            formatted_date_key = self.format_date(int(date_key))
                            cleaned_date = self.format_date(int(date_obj['date']))
                            date_obj.update({'formatted_date': cleaned_date})
                            formatted_type_obj.update({formatted_date_key: date_obj})
                        event_obj.update({type_key: formatted_type_obj})
                    dict_ent = {k: event_obj}
            elif 'date' in k.lower():
                if v is not None:
                    cleaned_date = self.format_date(v)
                    dict_ent = {k: {'formatted_date': cleaned_date, 'date': v}}
                else:
                    if last_attempt is False:
                        return None
                    else:
                        dict_ent = {k: {'formatted_date': None, 'date': v}}
            elif isinstance(v, list):
                sub_dict_list = []
                for sub_dict in v:
                    sub_dict['formatted_date'] = self.format_date(sub_dict['date'])
                    sub_dict_list.append(sub_dict)
                dict_ent = {k: sub_dict_list}
            else:
                dict_ent = {k: v}
            data.update(dict_ent)
        return data

    # Private Static Method to build API url for GET Request
    def _build_api_url(self, hist_obj, up_ticker, v="2", events=None):
        if events is None:
            events = ["div", "split", "earn"]
        event_str = ''
        for idx, s in enumerate(events, start=1):
            if idx < len(events):
                event_str += s + "|"
            elif idx == len(events):
                event_str += s
        base_url = "https://query" + v + ".finance.yahoo.com/v8/finance/chart/"
        api_url = base_url + up_ticker + '?symbol=' + up_ticker + '&period1=' + str(hist_obj['start']) + '&period2=' + \
                  str(hist_obj['end']) + '&interval=' + hist_obj['interval']
        country_ent = COUNTRY_MAP.get(self.country.upper())
        meta_str = '&lang=' + country_ent.get("lang", "en-US") + '&region=' + country_ent.get("region", "US")
        api_url += '&events=' + event_str + meta_str
        return api_url

    # Private Method to get financial data via API Call
    def _get_api_data(self, api_url, tries=0):
        if tries == 0 and self._cache.get(api_url):
            return self._cache[api_url]
        cur_url = api_url
        if tries > 0 and tries % 2 == 0:
            if 'query2.' in cur_url:
                cur_url = cur_url.replace("query2.", "query1.")
            elif 'query1.' in cur_url:
                cur_url = cur_url.replace("query1.", "query2.")
        urlopener = UrlOpener(self.session)
        response = urlopener.open(cur_url, proxy=self._get_proxy(), timeout=self.timeout)
        if response.status_code == 200:
            res_content = response.text
            response.close()
            data = loads(res_content)
            self._cache[api_url] = data
            return data
        else:
            if tries < 5:
                time.sleep(random.randrange(1, 5))
                response.close()
                time.sleep(random.randrange(1, 5))
                tries += 1
                return self._get_api_data(api_url, tries)
            else:
                response.close()
                return None

    # Private Method to clean API data
    def _clean_api_data(self, api_url):
        raw_data = self._get_api_data(api_url)
        ret_obj = {}
        ret_obj.update({'eventsData': []})
        if raw_data is None:
            return ret_obj
        results = raw_data['chart']['result']
        if results is None:
            return ret_obj
        for result in results:
            tz_sub_dict = {}
            ret_obj.update({'eventsData': result.get('events', {})})
            ret_obj.update({'firstTradeDate': result['meta'].get('firstTradeDate', 'NA')})
            ret_obj.update({'currency': result['meta'].get('currency', 'NA')})
            ret_obj.update({'instrumentType': result['meta'].get('instrumentType', 'NA')})
            tz_sub_dict.update({'gmtOffset': result['meta']['gmtoffset']})
            ret_obj.update({'timeZone': tz_sub_dict})
            timestamp_list = result['timestamp']
            high_price_list = result['indicators']['quote'][0]['high']
            low_price_list = result['indicators']['quote'][0]['low']
            open_price_list = result['indicators']['quote'][0]['open']
            close_price_list = result['indicators']['quote'][0]['close']
            volume_list = result['indicators']['quote'][0]['volume']
            adj_close_list = result['indicators']['adjclose'][0]['adjclose']
            i = 0
            prices_list = []
            for timestamp in timestamp_list:
                price_dict = {}
                price_dict.update({'date': timestamp})
                price_dict.update({'high': high_price_list[i]})
                price_dict.update({'low': low_price_list[i]})
                price_dict.update({'open': open_price_list[i]})
                price_dict.update({'close': close_price_list[i]})
                price_dict.update({'volume': volume_list[i]})
                price_dict.update({'adjclose': adj_close_list[i]})
                prices_list.append(price_dict)
                i += 1
            ret_obj.update({'prices': prices_list})
        return ret_obj

    # Private Method to Handle Recursive API Request
    def _recursive_api_request(self, hist_obj, up_ticker, clean=True, i=0):
        v = "2"
        if clean:
            re_data = self._clean_api_data(self._build_api_url(hist_obj, up_ticker, v))
            cleaned_re_data = self._clean_historical_data(re_data)
            if cleaned_re_data is not None:
                return cleaned_re_data
        else:
            re_data = self._get_api_data(self._build_api_url(hist_obj, up_ticker, v))
            if re_data is not None:
                return re_data
        if i < 6:
            i += 1
            return self._recursive_api_request(hist_obj, up_ticker, clean, i)
        elif clean:
            return self._clean_historical_data(re_data, True)

    # Private Method to take scrapped data and build a data dictionary with, used by get_stock_data()
    def _create_dict_ent(self, up_ticker, statement_type, tech_type, report_name, hist_obj):
        if statement_type == 'history':
            try:
                cleaned_re_data = self._recursive_api_request(hist_obj, up_ticker)
            except KeyError:
                cleaned_re_data = None
            return {up_ticker: cleaned_re_data}
        else:
            dict_ent = {}
            params = {}
            r_map = get_request_config(tech_type, REQUEST_MAP)
            r_cat = None
            if statement_type != 'analytic':
                r_cat = get_request_category(tech_type, self.YAHOO_FINANCIAL_TYPES, statement_type)
            YAHOO_URL = self._construct_url(
                up_ticker.lower(),
                r_map,
                params,
                hist_obj.get("interval"),
                r_cat
            )
            if tech_type == '' and statement_type != 'history':
                try:
                    re_data = self._get_historical_data(YAHOO_URL, REQUEST_MAP['fundamentals'], tech_type,
                                                        statement_type)
                    dict_ent = {up_ticker: re_data, 'dataType': report_name}
                except KeyError:
                    re_data = None
                    dict_ent = {up_ticker: re_data, 'dataType': report_name}
            elif tech_type != '' and statement_type != 'history':
                r_map = get_request_config(tech_type, REQUEST_MAP)
                try:
                    re_data = self._get_historical_data(YAHOO_URL, r_map, tech_type, statement_type)
                except KeyError:
                    re_data = None
                dict_ent = {up_ticker: re_data}
            return dict_ent

    def _retry_create_dict_ent(self, up_ticker, statement_type, tech_type, report_name, hist_obj):
        i = 0
        while i < 250:
            try:
                out = self._create_dict_ent(up_ticker, statement_type, tech_type, report_name, hist_obj)
                return out
            except:
                time.sleep(random.randint(2, 10))
                i += 1
                continue

    # Private method to return the stmt_id for the reformat_process
    def _get_stmt_id(self, statement_type, raw_data):
        stmt_id = ''
        i = 0
        for key in raw_data.keys():
            if key in self.YAHOO_FINANCIAL_TYPES[statement_type.lower()]:
                stmt_id = key
                i += 1
        if i != 1:
            return None
        return stmt_id

    # Private Method for the Reformat Process
    @staticmethod
    def _reformat_stmt_data_process(raw_data):
        final_data_list = []
        if raw_data is not None:
            for date_key, data_item in raw_data.items():
                dict_item = {date_key: data_item}
                final_data_list.append(dict_item)
            return final_data_list
        else:
            return raw_data

    # Private Method for the Flat Reformat Process
    @staticmethod
    def _reformat_stmt_data_process_flat(raw_data):
        final_data = {}
        if raw_data is not None:
            for date_key, data_item in raw_data.items():
                final_data.update({date_key: data_item})
            return final_data
        else:
            return raw_data

    # Private Method to return subdict entry for the statement reformat process
    def _get_sub_dict_ent(self, ticker, raw_data):
        if self.flat_format:
            form_data_dict = self._reformat_stmt_data_process_flat(raw_data[ticker])
            return {ticker: form_data_dict}
        form_data_list = self._reformat_stmt_data_process(raw_data[ticker])
        return {ticker: form_data_list}

    # Public method to get time interval code
    def get_time_code(self, time_interval):
        interval_code = self._INTERVAL_DICT[time_interval.lower()]
        return interval_code

    # Public Method to get stock data
    def get_stock_data(self, statement_type='income', tech_type='', report_name='', hist_obj={}):
        data = {}
        if statement_type == 'income' and tech_type == '' and report_name == '':  # temp, so this method doesn't return nulls
            statement_type = 'profile'
            tech_type = 'assetProfile'
            report_name = 'assetProfile'
        if isinstance(self.ticker, str):
            dict_ent = self._retry_create_dict_ent(self.ticker, statement_type, tech_type, report_name, hist_obj)
            data.update(dict_ent)
        else:
            if self.concurrent:
                with Pool(self._get_worker_count()) as pool:
                    dict_ents = pool.map(partial(self._retry_create_dict_ent,
                                                 statement_type=statement_type,
                                                 tech_type=tech_type,
                                                 report_name=report_name,
                                                 hist_obj=hist_obj), self.ticker)
                    for dict_ent in dict_ents:
                        data.update(dict_ent)
                    pool.close()
                    pool.join()
            else:
                for tick in self.ticker:
                    try:
                        dict_ent = self._create_dict_ent(tick, statement_type, tech_type, report_name, hist_obj)
                        data.update(dict_ent)
                    except ManagedException:
                        logging.info("yahoofinancials ticker: %s error getting %s - %s\n\tContinuing extraction...",
                                     str(tick), statement_type, str(ManagedException))
                        continue
        return data

    # Public Method to get technical stock data
    def get_stock_tech_data(self, tech_type):
        if tech_type == 'defaultKeyStatistics':
            return self.get_stock_data(statement_type='keystats', tech_type=tech_type)
        else:
            return self.get_stock_data(tech_type=tech_type)

    # Public Method to get reformatted statement data
    def get_reformatted_stmt_data(self, raw_data):
        sub_dict, data_dict = {}, {}
        data_type = raw_data['dataType']
        if isinstance(self.ticker, str):
            sub_dict_ent = self._get_sub_dict_ent(self.ticker, raw_data)
            sub_dict.update(sub_dict_ent)
            dict_ent = {data_type: sub_dict}
            data_dict.update(dict_ent)
        else:
            if self.concurrent:
                with Pool(self._get_worker_count()) as pool:
                    sub_dict_ents = pool.map(partial(self._get_sub_dict_ent,
                                                     raw_data=raw_data), self.ticker)
                    for dict_ent in sub_dict_ents:
                        sub_dict.update(dict_ent)
                    pool.close()
                    pool.join()
            else:
                for tick in self.ticker:
                    sub_dict_ent = self._get_sub_dict_ent(tick, raw_data)
                    sub_dict.update(sub_dict_ent)
            dict_ent = {data_type: sub_dict}
            data_dict.update(dict_ent)
        return data_dict

    # Public method to get cleaned report data
    def _clean_data_process(self, tick, report_type, raw_report_data):
        if report_type == 'earnings':
            try:
                cleaned_data = self._clean_earnings_data(raw_report_data[tick])
            except:
                cleaned_data = None
        else:
            try:
                cleaned_data = self._clean_reports(raw_report_data[tick])
            except:
                cleaned_data = None
        return cleaned_data

    # Public method to get cleaned summary and price report data
    def get_clean_data(self, raw_report_data, report_type):
        cleaned_data_dict = {}
        if isinstance(self.ticker, str):
            cleaned_data = self._clean_data_process(self.ticker, report_type, raw_report_data)
            cleaned_data_dict.update({self.ticker: cleaned_data})
        else:
            if self.concurrent:
                with Pool(self._get_worker_count()) as pool:
                    cleaned_data_list = pool.map(partial(self._clean_data_process,
                                                         report_type=report_type,
                                                         raw_report_data=raw_report_data), self.ticker)
                    for idx, cleaned_data in enumerate(cleaned_data_list):
                        cleaned_data_dict.update({self.ticker[idx]: cleaned_data})
                    pool.close()
                    pool.join()
            else:
                for tick in self.ticker:
                    cleaned_data = self._clean_data_process(tick, report_type, raw_report_data)
                    cleaned_data_dict.update({tick: cleaned_data})
        return cleaned_data_dict

    # Private method to handle dividend data requests
    def _handle_api_dividend_request(self, cur_ticker, start, end, interval):
        re_dividends = []
        hist_obj = {"start": start, "end": end, "interval": interval}
        div_dict = self._recursive_api_request(hist_obj, cur_ticker, False)['chart']['result'][0]['events']['dividends']
        for div_time_key, div_obj in div_dict.items():
            dividend_obj = {
                'date': div_obj['date'],
                'formatted_date': self.format_date(int(div_obj['date'])),
                'amount': div_obj.get('amount', None)
            }
            re_dividends.append(dividend_obj)
        return sorted(re_dividends, key=lambda div: div['date'])

    # Public method to get daily dividend data
    def get_stock_dividend_data(self, start, end, interval):
        interval_code = self.get_time_code(interval)
        if isinstance(self.ticker, str):
            try:
                return {self.ticker: self._handle_api_dividend_request(self.ticker, start, end, interval_code)}
            except:
                return {self.ticker: None}
        else:
            re_data = {}
            if self.concurrent:
                with Pool(self._get_worker_count()) as pool:
                    div_data_list = pool.map(partial(self._handle_api_dividend_request,
                                                     start=start,
                                                     end=end,
                                                     interval=interval_code), self.ticker)
                    for idx, div_data in enumerate(div_data_list):
                        re_data.update({self.ticker[idx]: div_data})
                    pool.close()
                    pool.join()
            else:
                for tick in self.ticker:
                    try:
                        div_data = self._handle_api_dividend_request(tick, start, end, interval_code)
                        re_data.update({tick: div_data})
                    except:
                        re_data.update({tick: None})
            return re_data
