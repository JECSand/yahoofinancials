"""
==============================
The Yahoo Financials Module
Version: 1.7
==============================

Author: Connor Sanders
Email: sandersconnor1@gmail.com
Version Released: 01/01/2023
Tested on Python 3.6, 3.7, 3.8, 3.9, and 3.10

Copyright (c) 2023 Connor Sanders
MIT License

List of Included Functions:

1) get_financial_stmts(frequency, statement_type, reformat=True)
   - frequency can be either 'annual' or 'quarterly'.
   - statement_type can be 'income', 'balance', 'cash'.
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
2) get_stock_price_data(reformat=True)
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
3) get_stock_earnings_data(reformat=True)
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
4) get_summary_data(reformat=True)
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
5) get_stock_quote_type_data()
6) get_historical_price_data(start_date, end_date, time_interval)
   - Gets historical price data for currencies, stocks, indexes, cryptocurrencies, and commodity futures.
   - start_date should be entered in the 'YYYY-MM-DD' format. First day that financial data will be pulled.
   - end_date should be entered in the 'YYYY-MM-DD' format. Last day that financial data will be pulled.
   - time_interval can be either 'daily', 'weekly', or 'monthly'. Parameter determines the time period interval.

Usage Examples:
from yahoofinancials import YahooFinancials
#tickers = 'AAPL'
#or
tickers = ['AAPL', 'WFC', 'F', 'JPY=X', 'XRP-USD', 'GC=F']
yahoo_financials = YahooFinancials(tickers)
balance_sheet_data = yahoo_financials.get_financial_stmts('quarterly', 'balance')
earnings_data = yahoo_financials.get_stock_earnings_data()
historical_prices = yahoo_financials.get_historical_price_data('2015-01-15', '2017-10-15', 'weekly')
"""

import sys
import calendar
import re
from json import loads
import time
from bs4 import BeautifulSoup
import datetime
import pytz
import random
try:
    from urllib import FancyURLopener
except:
    from urllib.request import FancyURLopener

import hashlib
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json

# track the last get timestamp to add a minimum delay between gets - be nice!
_lastget = 0


# Custom Exception class to handle custom error
class ManagedException(Exception):
    pass


# Class used to open urls for financial data
class UrlOpener(FancyURLopener):
    version = 'w3m/0.5.3+git20180125'


# Class containing Yahoo Finance ETL Functionality
class YahooFinanceETL(object):

    def __init__(self, ticker):
        self.ticker = ticker.upper() if isinstance(ticker, str) else [t.upper() for t in ticker]
        self._cache = {}

    # Minimum interval between Yahoo Finance requests for this instance
    _MIN_INTERVAL = 7

    # Meta-data dictionaries for the classes to use
    YAHOO_FINANCIAL_TYPES = {
        'income': ['financials', 'incomeStatementHistory', 'incomeStatementHistoryQuarterly'],
        'balance': ['balance-sheet', 'balanceSheetHistory', 'balanceSheetHistoryQuarterly', 'balanceSheetStatements'],
        'cash': ['cash-flow', 'cashflowStatementHistory', 'cashflowStatementHistoryQuarterly', 'cashflowStatements'],
        'keystats': ['key-statistics'],
        'history': ['history']
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
        else:
            report_num = 2
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

    # Private method to scrape data from yahoo finance
    def _scrape_data(self, url, tech_type, statement_type):
        global _lastget
        if not self._cache.get(url):
            now = int(time.time())
            if _lastget and now - _lastget < self._MIN_INTERVAL:
                time.sleep(self._MIN_INTERVAL - (now - _lastget) + 1)
                now = int(time.time())
            _lastget = now
            urlopener = UrlOpener()
            # Try to open the URL up to 10 times sleeping random time if something goes wrong
            max_retry = 10
            for i in range(0, max_retry):
                response = urlopener.open(url)
                if response.getcode() != 200:
                    time.sleep(random.randrange(10, 20))
                else:
                    response_content = response.read()
                    soup = BeautifulSoup(response_content, "html.parser")
                    re_script = soup.find("script", text=re.compile("root.App.main"))
                    if re_script is not None:
                        script = re_script.text
                        # bs4 4.9.0 changed so text from scripts is no longer considered text
                        if not script:
                            script = re_script.string
                        self._cache[url] = loads(re.search("root.App.main\s+=\s+(\{.*\})", script).group(1))
                        response.close()
                        break
                    else:
                        time.sleep(random.randrange(10, 20))
                if i == max_retry - 1:
                    # Raise a custom exception if we can't get the web page within max_retry attempts
                    raise ManagedException("Server replied with HTTP " + str(response.getcode()) +
                                           " code while opening the url: " + str(url))
        data = self._cache[url]
        data = self._decryptData(data)
        if tech_type == '' and statement_type != 'history':
            stores = data["QuoteSummaryStore"]
        elif tech_type != '' and statement_type != 'history':
            stores = data["QuoteSummaryStore"][tech_type]
        else:
            stores = data["HistoricalPriceStore"]
        return stores

    def _decryptData(self,data):
        #function taken from another package at https://github.com/ranaroussi/yfinance/pull/1253/commits/8e5f0984af347afda6be74b27a989422e49a975b
        encrypted_stores = data['context']['dispatcher']['stores']
        _cs = data["_cs"]
        _cr = data["_cr"]

        _cr = b"".join(int.to_bytes(i, length=4, byteorder="big", signed=True) for i in json.loads(_cr)["words"])
        password = hashlib.pbkdf2_hmac("sha1", _cs.encode("utf8"), _cr, 1, dklen=32).hex()

        encrypted_stores = b64decode(encrypted_stores)
        assert encrypted_stores[0:8] == b"Salted__"
        salt = encrypted_stores[8:16]
        encrypted_stores = encrypted_stores[16:]

        def EVPKDF(
            password,
            salt,
            keySize=32,
            ivSize=16,
            iterations=1,
            hashAlgorithm="md5",
        ) -> tuple:
            """OpenSSL EVP Key Derivation Function
            Args:
                password (Union[str, bytes, bytearray]): Password to generate key from.
                salt (Union[bytes, bytearray]): Salt to use.
                keySize (int, optional): Output key length in bytes. Defaults to 32.
                ivSize (int, optional): Output Initialization Vector (IV) length in bytes. Defaults to 16.
                iterations (int, optional): Number of iterations to perform. Defaults to 1.
                hashAlgorithm (str, optional): Hash algorithm to use for the KDF. Defaults to 'md5'.
            Returns:
                key, iv: Derived key and Initialization Vector (IV) bytes.
            Taken from: https://gist.github.com/rafiibrahim8/0cd0f8c46896cafef6486cb1a50a16d3
            OpenSSL original code: https://github.com/openssl/openssl/blob/master/crypto/evp/evp_key.c#L78
            """

            assert iterations > 0, "Iterations can not be less than 1."

            if isinstance(password, str):
                password = password.encode("utf-8")

            final_length = keySize + ivSize
            key_iv = b""
            block = None

            while len(key_iv) < final_length:
                hasher = hashlib.new(hashAlgorithm)
                if block:
                    hasher.update(block)
                hasher.update(password)
                hasher.update(salt)
                block = hasher.digest()
                for _ in range(1, iterations):
                    block = hashlib.new(hashAlgorithm, block).digest()
                key_iv += block

            key, iv = key_iv[:keySize], key_iv[keySize:final_length]
            return key, iv

        key, iv = EVPKDF(password, salt, keySize=32, ivSize=16, iterations=1, hashAlgorithm="md5")

        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        plaintext = cipher.decrypt(encrypted_stores)
        plaintext = unpad(plaintext, 16, style="pkcs7")
        decoded_stores = json.loads(plaintext)

        return decoded_stores

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
        utc_dt = self._convert_to_utc(form_date_time)
        return utc_dt

    # Private method to return the a sub dictionary entry for the earning report cleaning
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
        sub_ent = {key: sub_list}
        return sub_ent

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
            # Python 2 and Unicode
            elif sys.version_info < (3, 0) and isinstance(v, unicode):
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

    # Private method to get time interval code
    def _build_historical_url(self, ticker, hist_oj):
        url = self._BASE_YAHOO_URL + self._encode_ticker(ticker) + '/history?period1=' + str(hist_oj['start']) + \
              '&period2=' + str(hist_oj['end']) + '&interval=' + hist_oj['interval'] + '&filter=history&frequency=' + \
              hist_oj['interval']
        return url

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
    @staticmethod
    def _build_api_url(hist_obj, up_ticker):
        base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        api_url = base_url + up_ticker + '?symbol=' + up_ticker + '&period1=' + str(hist_obj['start']) + '&period2=' + \
                  str(hist_obj['end']) + '&interval=' + hist_obj['interval']
        api_url += '&events=div|split|earn&lang=en-US&region=US'
        return api_url

    # Private Method to get financial data via API Call
    def _get_api_data(self, api_url, tries=0):
        urlopener = UrlOpener()
        response = urlopener.open(api_url)
        if response.getcode() == 200:
            res_content = response.read()
            response.close()
            if sys.version_info < (3, 0):
                return loads(res_content)
            return loads(res_content.decode('utf-8'))
        else:
            if tries < 5:
                time.sleep(random.randrange(10, 20))
                tries += 1
                return self._get_api_data(api_url, tries)
            else:
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
    def _recursive_api_request(self, hist_obj, up_ticker, i=0):
        api_url = self._build_api_url(hist_obj, up_ticker)
        re_data = self._clean_api_data(api_url)
        cleaned_re_data = self._clean_historical_data(re_data)
        if cleaned_re_data is not None:
            return cleaned_re_data
        else:
            if i < 3:
                i += 1
                return self._recursive_api_request(hist_obj, up_ticker, i)
            else:
                return self._clean_historical_data(re_data, True)

    # Private Method to take scrapped data and build a data dictionary with
    def _create_dict_ent(self, up_ticker, statement_type, tech_type, report_name, hist_obj):
        YAHOO_URL = self._BASE_YAHOO_URL + up_ticker + '/' + self.YAHOO_FINANCIAL_TYPES[statement_type][0] + '?p=' +\
                    up_ticker
        if tech_type == '' and statement_type != 'history':
            try:
                re_data = self._scrape_data(YAHOO_URL, tech_type, statement_type)
                dict_ent = {up_ticker: re_data[u'' + report_name], 'dataType': report_name}
            except KeyError:
                re_data = None
                dict_ent = {up_ticker: re_data, 'dataType': report_name}
        elif tech_type != '' and statement_type != 'history':
            try:
                re_data = self._scrape_data(YAHOO_URL, tech_type, statement_type)
            except KeyError:
                re_data = None
            dict_ent = {up_ticker: re_data}
        else:
            YAHOO_URL = self._build_historical_url(up_ticker, hist_obj)
            try:
                cleaned_re_data = self._recursive_api_request(hist_obj, up_ticker)
            except KeyError:
                try:
                    re_data = self._scrape_data(YAHOO_URL, tech_type, statement_type)
                    cleaned_re_data = self._clean_historical_data(re_data)
                except KeyError:
                    cleaned_re_data = None
            dict_ent = {up_ticker: cleaned_re_data}
        return dict_ent

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
    def _reformat_stmt_data_process(self, raw_data, statement_type):
        final_data_list = []
        if raw_data is not None:
            stmt_id = self._get_stmt_id(statement_type, raw_data)
            if stmt_id is None:
                return final_data_list
            hashed_data_list = raw_data[stmt_id]
            for data_item in hashed_data_list:
                data_date = ''
                sub_data_dict = {}
                for k, v in data_item.items():
                    if k == 'endDate':
                        data_date = v['fmt']
                    elif k != 'maxAge':
                        numerical_val = self._determine_numeric_value(v)
                        sub_dict_item = {k: numerical_val}
                        sub_data_dict.update(sub_dict_item)
                dict_item = {data_date: sub_data_dict}
                final_data_list.append(dict_item)
            return final_data_list
        else:
            return raw_data

    # Private Method to return subdict entry for the statement reformat process
    def _get_sub_dict_ent(self, ticker, raw_data, statement_type):
        form_data_list = self._reformat_stmt_data_process(raw_data[ticker], statement_type)
        return {ticker: form_data_list}

    # Public method to get time interval code
    def get_time_code(self, time_interval):
        interval_code = self._INTERVAL_DICT[time_interval.lower()]
        return interval_code

    # Public Method to get stock data
    def get_stock_data(self, statement_type='income', tech_type='', report_name='', hist_obj={}):
        data = {}
        if isinstance(self.ticker, str):
            dict_ent = self._create_dict_ent(self.ticker, statement_type, tech_type, report_name, hist_obj)
            data.update(dict_ent)
        else:
            for tick in self.ticker:
                try:
                    dict_ent = self._create_dict_ent(tick, statement_type, tech_type, report_name, hist_obj)
                    data.update(dict_ent)
                except ManagedException:
                    print("Warning! Ticker: " + str(tick) + " error - " + str(ManagedException))
                    print("The process is still running...")
                    continue
        return data

    # Public Method to get technical stock data
    def get_stock_tech_data(self, tech_type):
        if tech_type == 'defaultKeyStatistics':
            return self.get_stock_data(statement_type='keystats', tech_type=tech_type)
        else:
            return self.get_stock_data(tech_type=tech_type)

    # Public Method to get reformatted statement data
    def get_reformatted_stmt_data(self, raw_data, statement_type):
        data_dict = {}
        sub_dict = {}
        data_type = raw_data['dataType']
        if isinstance(self.ticker, str):
            sub_dict_ent = self._get_sub_dict_ent(self.ticker, raw_data, statement_type)
            sub_dict.update(sub_dict_ent)
            dict_ent = {data_type: sub_dict}
            data_dict.update(dict_ent)
        else:
            for tick in self.ticker:
                sub_dict_ent = self._get_sub_dict_ent(tick, raw_data, statement_type)
                sub_dict.update(sub_dict_ent)
            dict_ent = {data_type: sub_dict}
            data_dict.update(dict_ent)
        return data_dict

    # Public method to get cleaned summary and price report data
    def get_clean_data(self, raw_report_data, report_type):
        cleaned_data_dict = {}
        if isinstance(self.ticker, str):
            if report_type == 'earnings':
                try:
                    cleaned_data = self._clean_earnings_data(raw_report_data[self.ticker])
                except:
                    cleaned_data = None
            else:
                try:
                    cleaned_data = self._clean_reports(raw_report_data[self.ticker])
                except:
                    cleaned_data = None
            cleaned_data_dict.update({self.ticker: cleaned_data})
        else:
            for tick in self.ticker:
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
                cleaned_data_dict.update({tick: cleaned_data})
        return cleaned_data_dict

    # Private method to handle dividend data requests
    def _handle_api_dividend_request(self, cur_ticker, start, end, interval):
        re_dividends = []
        test_url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + cur_ticker + \
                   '?period1=' + str(start) + '&period2=' + str(end) + '&interval=' + interval + '&events=div'
        div_dict = self._get_api_data(test_url)['chart']['result'][0]['events']['dividends']
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
            for tick in self.ticker:
                try:
                    div_data = self._handle_api_dividend_request(tick, start, end, interval_code)
                    re_data.update({tick: div_data})
                except:
                    re_data.update({tick: None})
            return re_data


# Class containing methods to create stock data extracts
class YahooFinancials(YahooFinanceETL):

    # Private method that handles financial statement extraction
    def _run_financial_stmt(self, statement_type, report_num, reformat):
        report_name = self.YAHOO_FINANCIAL_TYPES[statement_type][report_num]
        if reformat:
            raw_data = self.get_stock_data(statement_type, report_name=report_name)
            data = self.get_reformatted_stmt_data(raw_data, statement_type)
        else:
            data = self.get_stock_data(statement_type, report_name=report_name)
        return data

    # Public Method for the user to get financial statement data
    def get_financial_stmts(self, frequency, statement_type, reformat=True):
        report_num = self.get_report_type(frequency)
        if isinstance(statement_type, str):
            data = self._run_financial_stmt(statement_type, report_num, reformat)
        else:
            data = {}
            for stmt_type in statement_type:
                re_data = self._run_financial_stmt(stmt_type, report_num, reformat)
                data.update(re_data)
        return data

    # Public Method for the user to get stock price data
    def get_stock_price_data(self, reformat=True):
        if reformat:
            return self.get_clean_data(self.get_stock_tech_data('price'), 'price')
        else:
            return self.get_stock_tech_data('price')

    # Public Method for the user to return key-statistics data
    def get_key_statistics_data(self, reformat=True):
        if reformat:
            return self.get_clean_data(self.get_stock_tech_data('defaultKeyStatistics'), 'defaultKeyStatistics')
        else:
            return self.get_stock_tech_data('defaultKeyStatistics')

    # Public Method for the user to get stock earnings data
    def get_stock_earnings_data(self, reformat=True):
        if reformat:
            return self.get_clean_data(self.get_stock_tech_data('earnings'), 'earnings')
        else:
            return self.get_stock_tech_data('earnings')

    # Public Method for the user to get stock summary data
    def get_summary_data(self, reformat=True):
        if reformat:
            return self.get_clean_data(self.get_stock_tech_data('summaryDetail'), 'summaryDetail')
        else:
            return self.get_stock_tech_data('summaryDetail')

    # Public Method for the user to get the yahoo summary url
    def get_stock_summary_url(self):
        if isinstance(self.ticker, str):
            return self._BASE_YAHOO_URL + self.ticker
        return {t: self._BASE_YAHOO_URL + t for t in self.ticker}

    # Public Method for the user to get stock quote data
    def get_stock_quote_type_data(self):
        return self.get_stock_tech_data('quoteType')

    # Public Method for user to get historical price data with
    def get_historical_price_data(self, start_date, end_date, time_interval):
        interval_code = self.get_time_code(time_interval)
        start = self.format_date(start_date)
        end = self.format_date(end_date)
        hist_obj = {'start': start, 'end': end, 'interval': interval_code}
        return self.get_stock_data('history', hist_obj=hist_obj)

    # Private Method for Functions needing stock_price_data
    def _stock_price_data(self, data_field):
        if isinstance(self.ticker, str):
            if self.get_stock_price_data()[self.ticker] is None:
                return None
            return self.get_stock_price_data()[self.ticker].get(data_field, None)
        else:
            ret_obj = {}
            for tick in self.ticker:
                if self.get_stock_price_data()[tick] is None:
                    ret_obj.update({tick: None})
                else:
                    ret_obj.update({tick: self.get_stock_price_data()[tick].get(data_field, None)})
            return ret_obj

    # Private Method for Functions needing stock_price_data
    def _stock_summary_data(self, data_field):
        if isinstance(self.ticker, str):
            if self.get_summary_data()[self.ticker] is None:
                return None
            return self.get_summary_data()[self.ticker].get(data_field, None)
        else:
            ret_obj = {}
            for tick in self.ticker:
                if self.get_summary_data()[tick] is None:
                    ret_obj.update({tick: None})
                else:
                    ret_obj.update({tick: self.get_summary_data()[tick].get(data_field, None)})
            return ret_obj

    # Private Method for Functions needing financial statement data
    def _financial_statement_data(self, stmt_type, stmt_code, field_name, freq):
        re_data = self.get_financial_stmts(freq, stmt_type)[stmt_code]
        if isinstance(self.ticker, str):
            try:
                date_key = re_data[self.ticker][0].keys()[0]
            except (IndexError, AttributeError, TypeError):
                date_key = list(re_data[self.ticker][0])[0]
            data = re_data[self.ticker][0][date_key][field_name]
        else:
            data = {}
            for tick in self.ticker:
                try:
                    date_key = re_data[tick][0].keys()[0]
                except:
                    try:
                        date_key = list(re_data[tick][0].keys())[0]
                    except:
                        date_key = None
                if date_key is not None:
                    sub_data = re_data[tick][0][date_key][field_name]
                    data.update({tick: sub_data})
                else:
                    data.update({tick: None})
        return data

    # Public method to get daily dividend data
    def get_daily_dividend_data(self, start_date, end_date):
        start = self.format_date(start_date)
        end = self.format_date(end_date)
        return self.get_stock_dividend_data(start, end, 'daily')

    # Public Price Data Methods
    def get_current_price(self):
        return self._stock_price_data('regularMarketPrice')

    def get_current_change(self):
        return self._stock_price_data('regularMarketChange')

    def get_current_percent_change(self):
        return self._stock_price_data('regularMarketChangePercent')

    def get_current_volume(self):
        return self._stock_price_data('regularMarketVolume')

    def get_prev_close_price(self):
        return self._stock_price_data('regularMarketPreviousClose')

    def get_open_price(self):
        return self._stock_price_data('regularMarketOpen')

    def get_ten_day_avg_daily_volume(self):
        return self._stock_price_data('averageDailyVolume10Day')

    def get_three_month_avg_daily_volume(self):
        return self._stock_price_data('averageDailyVolume3Month')

    def get_stock_exchange(self):
        return self._stock_price_data('exchangeName')

    def get_market_cap(self):
        return self._stock_price_data('marketCap')

    def get_daily_low(self):
        return self._stock_price_data('regularMarketDayLow')

    def get_daily_high(self):
        return self._stock_price_data('regularMarketDayHigh')

    def get_currency(self):
        return self._stock_price_data('currency')

    # Public Summary Data Methods
    def get_yearly_high(self):
        return self._stock_summary_data('fiftyTwoWeekHigh')

    def get_yearly_low(self):
        return self._stock_summary_data('fiftyTwoWeekLow')

    def get_dividend_yield(self):
        return self._stock_summary_data('dividendYield')

    def get_annual_avg_div_yield(self):
        return self._stock_summary_data('trailingAnnualDividendYield')

    def get_five_yr_avg_div_yield(self):
        return self._stock_summary_data('fiveYearAvgDividendYield')

    def get_dividend_rate(self):
        return self._stock_summary_data('dividendRate')

    def get_annual_avg_div_rate(self):
        return self._stock_summary_data('trailingAnnualDividendRate')

    def get_50day_moving_avg(self):
        return self._stock_summary_data('fiftyDayAverage')

    def get_200day_moving_avg(self):
        return self._stock_summary_data('twoHundredDayAverage')

    def get_beta(self):
        return self._stock_summary_data('beta')

    def get_payout_ratio(self):
        return self._stock_summary_data('payoutRatio')

    def get_pe_ratio(self):
        return self._stock_summary_data('trailingPE')

    def get_price_to_sales(self):
        return self._stock_summary_data('priceToSalesTrailing12Months')

    def get_exdividend_date(self):
        return self._stock_summary_data('exDividendDate')

    # Financial Statement Data Methods
    def get_book_value(self):
        return self._financial_statement_data('balance', 'balanceSheetHistoryQuarterly',
                                              'totalStockholderEquity', 'quarterly')

    def get_ebit(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'ebit', 'annual')

    def get_net_income(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'netIncome', 'annual')

    def get_interest_expense(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'interestExpense', 'annual')

    def get_operating_income(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'operatingIncome', 'annual')

    def get_total_operating_expense(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'totalOperatingExpenses', 'annual')

    def get_total_revenue(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'totalRevenue', 'annual')

    def get_cost_of_revenue(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'costOfRevenue', 'annual')

    def get_income_before_tax(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'incomeBeforeTax', 'annual')

    def get_income_tax_expense(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'incomeTaxExpense', 'annual')

    def get_gross_profit(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'grossProfit', 'annual')

    def get_net_income_from_continuing_ops(self):
        return self._financial_statement_data('income', 'incomeStatementHistory',
                                              'netIncomeFromContinuingOps', 'annual')

    def get_research_and_development(self):
        return self._financial_statement_data('income', 'incomeStatementHistory', 'researchDevelopment', 'annual')

    # Calculated Financial Methods
    def get_earnings_per_share(self):
        price_data = self.get_current_price()
        pe_ratio = self.get_pe_ratio()
        if isinstance(self.ticker, str):
            if price_data is not None and pe_ratio is not None:
                return price_data / pe_ratio
            else:
                return None
        else:
            ret_obj = {}
            for tick in self.ticker:
                if price_data[tick] is not None and pe_ratio[tick] is not None:
                    ret_obj.update({tick: price_data[tick] / pe_ratio[tick]})
                else:
                    ret_obj.update({tick: None})
            return ret_obj

    def get_num_shares_outstanding(self, price_type='current'):
        today_low = self._stock_summary_data('dayHigh')
        today_high = self._stock_summary_data('dayLow')
        cur_market_cap = self._stock_summary_data('marketCap')
        if isinstance(self.ticker, str):
            if cur_market_cap is not None:
                if price_type == 'current':
                    current = self.get_current_price()
                    if current is not None:
                        today_average = current
                    else:
                        return None
                else:
                    if today_high is not None and today_low is not None:
                        today_average = (today_high + today_low) / 2
                    else:
                        return None
                return cur_market_cap / today_average
            else:
                return None
        else:
            ret_obj = {}
            for tick in self.ticker:
                if cur_market_cap[tick] is not None:
                    if price_type == 'current':
                        current = self.get_current_price()
                        if current[tick] is not None:
                            ret_obj.update({tick: cur_market_cap[tick] / current[tick]})
                        else:
                            ret_obj.update({tick: None})
                    else:
                        if today_low[tick] is not None and today_high[tick] is not None:
                            today_average = (today_high[tick] + today_low[tick]) / 2
                            ret_obj.update({tick: cur_market_cap[tick] / today_average})
                        else:
                            ret_obj.update({tick: None})
                else:
                    ret_obj.update({tick: None})
            return ret_obj
