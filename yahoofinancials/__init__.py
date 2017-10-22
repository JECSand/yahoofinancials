"""
==============================
The Yahoo Financials Module
Version: 0.1
==============================

Author: Connor Sanders
Email: connor@exceleri.com
Version Released: 10/22/2017
Tested on Python 2.7 and 3.5

Copyright (c) 2017 Connor Sanders
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
4) get_stock_summary_data(reformat=True)
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
5) get_stock_quote_type_data()
6) get_historical_stock_data(start_date, end_date, time_interval)
   - start_date should be entered in the 'YYYY-MM-DD' format. First day that stock data will be pulled.
   - end_date should be entered in the 'YYYY-MM-DD' format. Last day that stock data will be pulled.
   - time_interval can be either 'daily', 'weekly', or 'monthly'. Parameter determines the time period interval.

Usage Examples:
from yahoofinancials import YahooFinancials
#tickers = 'AAPL'
#or
tickers = ['AAPL', 'WFC', 'F']
yahoo_financials = YahooFinancials(tickers)
balance_sheet_data = yahoo_financials.get_financial_stmts('quarterly', 'balance')
earnings_data = yahoo_financials.get_stock_earnings_data()
historical_stock_prices = yahoo_financials.get_historical_stock_data('2015-01-15', '2017-10-15', 'weekly')
"""

import sys
import re
from json import loads
import time
from bs4 import BeautifulSoup
import requests
import datetime
from datetime import date


class YahooFinancials:

    def __init__(self, ticker):
        self.ticker = ticker

    # Base Yahoo Finance URL for the class to build on
    _BASE_YAHOO_URL = 'https://finance.yahoo.com/quote/'

    # Meta-data dictionaries for the class to use
    _YAHOO_FINANCIAL_TYPES = {
        'income': ['financials', 'incomeStatementHistory', 'incomeStatementHistoryQuarterly'],
        'balance': ['balance-sheet', 'balanceSheetHistory', 'balanceSheetHistoryQuarterly', 'balanceSheetStatements'],
        'cash': ['cash-flow', 'cashflowStatementHistory', 'cashflowStatementHistoryQuarterly', 'cashflowStatements'],
        'history': ['history']
    }
    _INTERVAL_DICT = {
        'daily': '1d',
        'weekly': '1wk',
        'monthly': '1mo'
    }

    # private static method to get the appropriate report type identifier
    @staticmethod
    def _get_report_type(frequency):
        if frequency == 'annual':
            report_num = 1
        else:
            report_num = 2
        return report_num

    # private static method to format date serial string to readable format and vice versa
    @staticmethod
    def _format_date(in_date, convert_type):
        if convert_type == 'standard':
            form_date = datetime.datetime.fromtimestamp(int(in_date)).strftime('%Y-%m-%d')
        else:
            split_date = in_date.split('-')
            d = date(int(split_date[0]), int(split_date[1]), int(split_date[2]))
            form_date = int(time.mktime(d.timetuple()))
        return form_date

    # private static method to scrap data from yahoo finance
    @staticmethod
    def _scrape_data(url, tech_type, statement_type):
        response = requests.get(url)
        time.sleep(7)
        soup = BeautifulSoup(response.content, "html.parser")
        script = soup.find("script", text=re.compile("root.App.main")).text
        data = loads(re.search("root.App.main\s+=\s+(\{.*\})", script).group(1))
        if tech_type == '' and statement_type != 'history':
            stores = data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"]
        elif tech_type != '' and statement_type != 'history':
            stores = data["context"]["dispatcher"]["stores"]["QuoteSummaryStore"][tech_type]
        else:
            stores = data["context"]["dispatcher"]["stores"]["HistoricalPriceStore"]
        return stores

    # Private static method to process raw earnings data and clean
    @staticmethod
    def _clean_earnings_data(raw_data):
        cleaned_data = {}
        earnings_key = 'earningsData'
        financials_key = 'financialsData'
        for k, v in raw_data.items():
            if k == 'earningsChart':
                sub_dict = {}
                for k2, v2 in v.items():
                    if k2 == 'quarterly':
                        sub_list = []
                        for rec in v2:
                            sub_sub_dict = {}
                            for k3, v3 in rec.items():
                                if k3 == 'date':
                                    sub_sub_dict_ent = {k3: v3}
                                else:
                                    if 'raw' in list(v3.keys()):
                                        numerical_val = v3['raw']
                                    else:
                                        numerical_val = None
                                    sub_sub_dict_ent = {k3: numerical_val}
                                sub_sub_dict.update(sub_sub_dict_ent)
                            sub_list.append(sub_sub_dict)
                        sub_ent = {k2: sub_list}
                    elif k2 == 'currentQuarterEstimate':
                        if 'raw' in list(v2.keys()):
                            numerical_val = v2['raw']
                        else:
                            numerical_val = None
                        sub_ent = {k2: numerical_val}
                    else:
                        sub_ent = {k2: v2}
                    sub_dict.update(sub_ent)
                dict_ent = {earnings_key: sub_dict}
                cleaned_data.update(dict_ent)
            elif k == 'financialsChart':
                sub_dict = {}
                for k2, v2, in v.items():
                    sub_list = []
                    for rec in v2:
                        sub_sub_dict = {}
                        for k3, v3 in rec.items():
                            if k3 == 'date':
                                sub_sub_dict_ent = {k3: str(v3)}
                            else:
                                if 'raw' in list(v3.keys()):
                                    numerical_val = v3['raw']
                                else:
                                    numerical_val = None
                                sub_sub_dict_ent = {k3: numerical_val}
                            sub_sub_dict.update(sub_sub_dict_ent)
                        sub_list.append(sub_sub_dict)
                    sub_ent = {k2: sub_list}
                    sub_dict.update(sub_ent)
                dict_ent = {financials_key: sub_dict}
                cleaned_data.update(dict_ent)
            else:
                if k != 'maxAge':
                    dict_ent = {k: v}
                    cleaned_data.update(dict_ent)
        return cleaned_data

    # Private static method to clean summary and price reports
    @staticmethod
    def _clean_reports(raw_data):
        cleaned_dict = {}
        for k, v in raw_data.items():
            if isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
                dict_ent = {k: v}
            elif v is None:
                dict_ent = {k: v}
            else:
                if 'raw' in list(v.keys()):
                    numerical_val = v['raw']
                else:
                    numerical_val = None
                dict_ent = {k: numerical_val}
            cleaned_dict.update(dict_ent)
        return cleaned_dict

    # Private method to get time interval code
    def _get_time_code(self, time_interval):
        interval_code = self._INTERVAL_DICT[time_interval.lower()]
        return interval_code

    # Private method to get time interval code
    def _build_historical_url(self, ticker, hist_oj):
        url = self._BASE_YAHOO_URL + ticker + '/history?period1=' + str(hist_oj['start']) + '&period2=' + \
              str(hist_oj['end']) + '&interval=' + hist_oj['interval'] + '&filter=history&frequency=' + \
              hist_oj['interval']
        return url

    # Private Method to clean the dates of the newly returns historical stock data into readable format
    def _clean_historical_data(self, hist_data):
        data = {}
        for k, v in hist_data.items():
            if 'date' in k.lower():
                cleaned_date = self._format_date(v, 'standard')
                dict_ent = {k: {u'' + 'formatted_date': cleaned_date, 'date': v}}
                data.update(dict_ent)
            elif isinstance(v, list):
                sub_dict_list = []
                for sub_dict in v:
                    sub_dict[u'' + 'formatted_date'] = self._format_date(sub_dict['date'], 'standard')
                    sub_dict_list.append(sub_dict)
                dict_ent = {k: sub_dict_list}
                data.update(dict_ent)
            else:
                dict_ent = {k: v}
                data.update(dict_ent)
        return data

    # Private Method to take scrapped data and build a data dictionary with
    def _create_dict_ent(self, ticker, statement_type, tech_type, report_name, hist_obj):
        up_ticker = ticker.upper()
        YAHOO_URL = self._BASE_YAHOO_URL + up_ticker + '/' + self._YAHOO_FINANCIAL_TYPES[statement_type][0] + '?p=' +\
                    up_ticker
        if tech_type == '' and statement_type != 'history':
            re_data = self._scrape_data(YAHOO_URL, tech_type, statement_type)
            dict_ent = {up_ticker: re_data[u'' + report_name], 'dataType': report_name}
        elif tech_type != '' and statement_type != 'history':
            re_data = self._scrape_data(YAHOO_URL, tech_type, statement_type)
            dict_ent = {up_ticker: re_data}
        else:
            YAHOO_URL = self._build_historical_url(up_ticker, hist_obj)
            re_data = self._scrape_data(YAHOO_URL, tech_type, statement_type)
            cleaned_re_data = self._clean_historical_data(re_data)
            dict_ent = {up_ticker: cleaned_re_data}
        return dict_ent

    # Private Method to get stock data
    def _get_stock_data(self, statement_type='income', tech_type='', report_name='', hist_obj={}):
        data = {}
        if isinstance(self.ticker, str):
            dict_ent = self._create_dict_ent(self.ticker, statement_type, tech_type, report_name, hist_obj)
            data.update(dict_ent)
        else:
            for tick in self.ticker:
                dict_ent = self._create_dict_ent(tick, statement_type, tech_type, report_name, hist_obj)
                data.update(dict_ent)
        return data

    # Private Method to get technical stock data
    def _get_stock_tech_data(self, tech_type):
        return self._get_stock_data(tech_type=tech_type)

    # Private method to return the stmt_id for the reformat_process
    def _get_stmt_id(self, statement_type, raw_data):
        stmt_id = ''
        i = 0
        for key in list(raw_data.keys()):
            if key in self._YAHOO_FINANCIAL_TYPES[statement_type.lower()]:
                stmt_id = key
                i += 1
        if i != 1:
            sys.exit(1)
        return stmt_id

    # Private Method for the Reformat Process
    def _reformat_stmt_data_process(self, raw_data, statement_type):
        final_data_list = []
        stmt_id = self._get_stmt_id(statement_type, raw_data)
        hashed_data_list = raw_data[stmt_id]
        for data_item in hashed_data_list:
            data_date = ''
            sub_data_dict = {}
            for k, v in data_item.items():
                if k == 'endDate':
                    data_date = v['fmt']
                elif k != 'maxAge':
                    if 'raw' in list(v.keys()):
                        numerical_val = v['raw']
                    else:
                        numerical_val = None
                    sub_dict_item = {k: numerical_val}
                    sub_data_dict.update(sub_dict_item)
            dict_item = {data_date: sub_data_dict}
            final_data_list.append(dict_item)
        return final_data_list

    # Private Method to return subdict entry for the statement reformat process
    def _get_sub_dict_ent(self, ticker, raw_data, statement_type):
        form_data_list = self._reformat_stmt_data_process(raw_data[ticker], statement_type)
        return {ticker: form_data_list}

    # Private Method to get reformatted statement data
    def _get_reformatted_stmt_data(self, raw_data, statement_type):
        data_dict = {}
        sub_dict = {}
        dataType = raw_data['dataType']
        if isinstance(self.ticker, str):
            sub_dict_ent = self._get_sub_dict_ent(self.ticker, raw_data, statement_type)
            sub_dict.update(sub_dict_ent)
            dict_ent = {dataType: sub_dict}
            data_dict.update(dict_ent)
        else:
            for tick in self.ticker:
                sub_dict_ent = self._get_sub_dict_ent(tick, raw_data, statement_type)
                sub_dict.update(sub_dict_ent)
            dict_ent = {dataType: sub_dict}
            data_dict.update(dict_ent)
        return data_dict

    # Private method to get cleaned summary and price report data
    def _get_clean_data(self, raw_report_data, report_type):
        cleaned_data_dict = {}
        if isinstance(self.ticker, str):
            if report_type == 'earnings':
                cleaned_data = self._clean_earnings_data(raw_report_data[self.ticker])
            else:
                cleaned_data = self._clean_reports(raw_report_data[self.ticker])
            cleaned_data_dict.update({self.ticker: cleaned_data})
        else:
            for tick in self.ticker:
                if report_type == 'earnings':
                    cleaned_data = self._clean_earnings_data(raw_report_data[tick])
                else:
                    cleaned_data = self._clean_reports(raw_report_data[tick])
                cleaned_data_dict.update({tick: cleaned_data})
        return cleaned_data_dict

    # Public Method for the user to get financial statement data
    def get_financial_stmts(self, frequency, statement_type, reformat=True):
        report_num = self._get_report_type(frequency)
        report_name = self._YAHOO_FINANCIAL_TYPES[statement_type][report_num]
        if reformat:
            raw_data = self._get_stock_data(statement_type, report_name=report_name)
            data = self._get_reformatted_stmt_data(raw_data, statement_type)
        else:
            data = self._get_stock_data(statement_type, report_name=report_name)
        return data

    # Public Method for the user to get stock price data
    def get_stock_price_data(self, reformat=True):
        if reformat:
            return self._get_clean_data(self._get_stock_tech_data('price'), 'price')
        else:
            return self._get_stock_tech_data('price')

    # Public Method for the user to get stock earnings data
    def get_stock_earnings_data(self, reformat=True):
        if reformat:
            return self._get_clean_data(self._get_stock_tech_data('earnings'), 'earnings')
        else:
            return self._get_stock_tech_data('earnings')

    # Public Method for the user to get stock summary data
    def get_stock_summary_data(self, reformat=True):
        if reformat:
            return self._get_clean_data(self._get_stock_tech_data('summaryDetail'), 'summaryDetail')
        else:
            return self._get_stock_tech_data('summaryDetail')

    # Public Method for the user to get stock quote data
    def get_stock_quote_type_data(self):
        return self._get_stock_tech_data('quoteType')

    # Public Method for user to get historical stock data with
    def get_historical_stock_data(self, start_date, end_date, time_interval):
        interval_code = self._get_time_code(time_interval)
        start = self._format_date(start_date, 'unixstamp')
        end = self._format_date(end_date, 'unixstamp')
        hist_obj = {'start': start, 'end': end, 'interval': interval_code}
        data = self._get_stock_data('history', hist_obj=hist_obj)
        return data
