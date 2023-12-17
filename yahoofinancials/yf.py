"""
==============================
The Yahoo Financials Module
Version: 1.20
==============================

Author: Connor Sanders
Email: jecsand@pm.me
Version Released: 12/17/2023
Tested on Python 3.7, 3.8, 3.9, 3.10, 3.11, and 3.12

Copyright (c) 2023 Connor Sanders
MIT License

List of Included Functions:

1) get_financial_stmts(frequency, statement_type, reformat=True)
   - frequency can be either 'annual' or 'quarterly'.
   - statement_type can be 'income', 'balance', 'cash'.
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
2) get_stock_price_data(reformat=True)
3) get_stock_earnings_data()
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

from yahoofinancials.calcs import num_shares_outstanding, eps
from yahoofinancials.data import YahooFinanceData

__version__ = "1.20"
__author__ = "Connor Sanders"


# Class containing methods to create stock data extracts
class YahooFinancials(YahooFinanceData):
    """
    Arguments
    ----------
    tickers: str or list
        Ticker or listed collection of tickers
    Keyword Arguments
    -----------------
    concurrent: bool, default False, optional
        Defines whether the requests are made synchronously or asynchronously.
    country: str, default 'US', optional
        This allows you to alter the region, lang, corsDomain parameter sent with each request based on selected country
    max_workers: int, default 8, optional
        Defines the number of workers used to make concurrent requests.
        Only relevant if concurrent=True
    timeout: int, default 30, optional
        Defines how long a request will stay open.
    proxies: str or list, default None, optional
        Defines any proxies to use during this instantiation.
    flat_format: bool, default False, optional
        If set to True, returns fundamental data in a flattened format, i.e. without the list of dicts.
    """

    # Private method that handles financial statement extraction
    def _run_financial_stmt(self, statement_type, report_num, frequency, reformat):
        hist_obj = {"interval": frequency}
        report_name = self.YAHOO_FINANCIAL_TYPES[statement_type][report_num]
        if reformat:
            raw_data = self.get_stock_data(statement_type, report_name=report_name, hist_obj=hist_obj)
            data = self.get_reformatted_stmt_data(raw_data)
        else:
            data = self.get_stock_data(statement_type, report_name=report_name, hist_obj=hist_obj)
        return data

    # Public Method for the user to get financial statement data
    def get_financial_stmts(self, frequency, statement_type, reformat=True):
        report_num = self.get_report_type(frequency)
        if isinstance(statement_type, str):
            data = self._run_financial_stmt(statement_type, report_num, frequency, reformat)
        else:
            data = {}
            for stmt_type in statement_type:
                re_data = self._run_financial_stmt(stmt_type, report_num, frequency, reformat)
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

    # Public Method for the user to get company profile data
    def get_stock_profile_data(self, reformat=True):
        if reformat:
            return self.get_clean_data(
                self.get_stock_data(statement_type='profile', tech_type='assetProfile', report_name='assetProfile'),
                'earnings')
        else:
            return self.get_stock_data(statement_type='profile', tech_type='assetProfile', report_name='assetProfile')

    # Public Method for the user to get stock earnings data
    def get_stock_earnings_data(self):
        return self.get_stock_tech_data('earnings')

    # Public Method for the user to return financial data
    def get_financial_data(self, reformat=True):
        if reformat:
            return self.get_clean_data(self.get_stock_data(statement_type='keystats', tech_type='financialData'),
                                       'financialData')
        else:
            return self.get_stock_data(statement_type='keystats', tech_type='financialData')

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

    # Public Method for the user to get stock quote data
    def get_esg_score_data(self):
        return self.get_stock_tech_data('esgScores')

    def _get_analytic_data(self, tech_type):
        return self.get_stock_data(statement_type='analytic', tech_type=tech_type)

    # Public Method for user to get historical price data with
    def get_historical_price_data(self, start_date, end_date, time_interval):
        interval_code = self.get_time_code(time_interval)
        start = self.format_date(start_date)
        end = self.format_date(end_date)
        hist_obj = {'start': start, 'end': end, 'interval': interval_code}
        return self.get_stock_data('history', hist_obj=hist_obj)

    # Private Method for Functions needing stock_price_data
    def _stock_price_data(self, data_field):
        price_data = self.get_stock_price_data()
        if isinstance(self.ticker, str):
            if price_data[self.ticker] is None:
                return None
            return price_data[self.ticker].get(data_field)
        else:
            ret_obj = {}
            for tick in self.ticker:
                if price_data[tick] is None:
                    ret_obj.update({tick: None})
                else:
                    ret_obj.update({tick: price_data[tick].get(data_field)})
            return ret_obj

    # Private Method for Functions needing stock_price_data
    def _stock_summary_data(self, data_field):
        sum_data = self.get_summary_data()
        if isinstance(self.ticker, str):
            if sum_data[self.ticker] is None:
                return None
            return sum_data[self.ticker].get(data_field, None)
        else:
            ret_obj = {}
            for tick in self.ticker:
                if sum_data[tick] is None:
                    ret_obj.update({tick: None})
                else:
                    ret_obj.update({tick: sum_data[tick].get(data_field, None)})
            return ret_obj

    # Private Method for Functions needing financial statement data
    def _financial_statement_data(self, stmt_type, stmt_code, field_name, freq):
        re_data = self.get_financial_stmts(freq, stmt_type)[stmt_code]
        if isinstance(self.ticker, str):
            try:
                date_key = re_data[self.ticker][0].keys()[0]
            except (IndexError, AttributeError, TypeError):
                date_key = list(re_data[self.ticker][0])[0]
            data = re_data[self.ticker][0][date_key].get(field_name)
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
        return self._stock_summary_data('averageDailyVolume10Day')

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
        return self._financial_statement_data('income', 'incomeStatementHistory', 'netIncomeContinuousOperations',
                                              'annual')

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

    def get_recommendations(self):
        return self._get_analytic_data("recommendations")

    def get_insights(self):
        return self._get_analytic_data("insights")

    # Calculated Financial Methods
    def get_earnings_per_share(self):
        price_data = self.get_current_price()
        pe_ratio = self.get_pe_ratio()
        if isinstance(self.ticker, str):
            return eps(price_data, pe_ratio)
        else:
            ret_obj = {}
            for tick in self.ticker:
                re_val = eps(price_data[tick], pe_ratio[tick])
                ret_obj.update({tick: re_val})
            return ret_obj

    def get_num_shares_outstanding(self, price_type='current'):
        today_low = self._stock_summary_data('dayHigh')
        today_high = self._stock_summary_data('dayLow')
        cur_market_cap = self._stock_summary_data('marketCap')
        current = self.get_current_price()
        if isinstance(self.ticker, str):
            return num_shares_outstanding(cur_market_cap, today_low, today_high, price_type, current)
        else:
            ret_obj = {}
            for tick in self.ticker:
                re_data = num_shares_outstanding(cur_market_cap[tick], today_low[tick],
                                                 today_high[tick], price_type, current[tick])
                ret_obj.update({tick: re_data})
            return ret_obj
