# YahooFinancials Unit Tests v1.16
# Version Released: 07/17/2023
# Author: Connor Sanders
# Tested on Python 3.7, 3.8, 3.9, 3.10, and 3.11
# Copyright (c) 2023 Connor Sanders <jecsand@pm.me>
# MIT License

from unittest import main as t_main, TestCase
from yahoofinancials import YahooFinancials as yf

# Test Configuration Variables
stocks = ['AAPL', 'MSFT', 'C', 'IL&FSTRANS.NS']
currencies = ['EURUSD=X', 'JPY=X', 'GBPUSD=X']
us_treasuries = ['^TNX', '^IRX', '^TYX']


# Global function to check Fundamental Test results
def check_fundamental(test_data, test_type):
    if test_type == 'bal':
        if 'balanceSheetHistoryQuarterly' in test_data and test_data['balanceSheetHistoryQuarterly']['C'] is not None:
            return True
        return False
    elif test_type == 'inc':
        if 'incomeStatementHistoryQuarterly' in test_data and \
                test_data['incomeStatementHistoryQuarterly']['C'] is not None:
            return True
        return False
    elif test_type == 'all':
        if 'balanceSheetHistoryQuarterly' in test_data and 'incomeStatementHistoryQuarterly' in test_data and \
                'cashflowStatementHistoryQuarterly' in test_data:
            return True
        return False


# Main Test Module Class
class TestModule(TestCase):

    def setUp(self):
        self.test_yf_stock_single = yf('C')
        self.test_yf_stock_multi = yf(stocks)
        self.test_yf_treasuries_single = yf('^IRX')
        self.test_yf_treasuries_multi = yf(us_treasuries)
        self.test_yf_currencies = yf(currencies)
        self.test_yf_concurrent = yf(stocks, concurrent=True)

    # Fundamentals Test
    def test_yf_fundamentals(self):
        # Single stock test
        single_balance_sheet_data_qt = self.test_yf_stock_single.get_financial_stmts('quarterly', 'balance')
        single_income_statement_data_qt = self.test_yf_stock_single.get_financial_stmts('quarterly', 'income')
        single_all_statement_data_qt = self.test_yf_stock_single.get_financial_stmts('quarterly',
                                                                                     ['income', 'cash', 'balance'])
        # Multi stock test
        multi_balance_sheet_data_qt = self.test_yf_stock_multi.get_financial_stmts('quarterly', 'balance')
        multi_income_statement_data_qt = self.test_yf_stock_multi.get_financial_stmts('quarterly', 'income')
        multi_all_statement_data_qt = self.test_yf_stock_multi.get_financial_stmts('quarterly',
                                                                                   ['income', 'cash', 'balance'])
        # Single stock check
        result = check_fundamental(single_balance_sheet_data_qt, 'bal')
        self.assertEqual(result, True)
        result = check_fundamental(single_income_statement_data_qt, 'inc')
        self.assertEqual(result, True)
        result = check_fundamental(single_all_statement_data_qt, 'all')
        self.assertEqual(result, True)

        # Multi stock check
        result = check_fundamental(multi_balance_sheet_data_qt, 'bal')
        self.assertEqual(result, True)
        result = check_fundamental(multi_income_statement_data_qt, 'inc')
        self.assertEqual(result, True)
        result = check_fundamental(multi_all_statement_data_qt, 'all')
        self.assertEqual(result, True)

    # Historical Price Test
    def test_yf_historical_price(self):
        single_stock_prices = self.test_yf_stock_single.get_historical_price_data('2015-01-15', '2017-10-15', 'weekly')
        expected = {'high': 49.099998474121094, 'volume': 125737200, 'formatted_date': '2015-01-12',
                    'low': 46.599998474121094, 'date': 1421038800,
                    'close': 47.61000061035156, 'open': 48.959999084472656}
        # ignore adjclose as it will change with every dividend paid in the future
        del single_stock_prices['C']['prices'][0]['adjclose']
        self.assertDictEqual(single_stock_prices['C']['prices'][0], expected)

    # Historical Stock Daily Dividend Test
    def test_yf_dividend_price(self):
        single_stock_dividend = self.test_yf_stock_single.get_daily_dividend_data('1986-09-15', '1987-09-15')
        expected = {"C": [{'date': 544714200, 'formatted_date': '1987-04-06', 'amount': 0.332},
                          {'date': 552576600, 'formatted_date': '1987-07-06', 'amount': 0.332}]}
        self.assertDictEqual(single_stock_dividend, expected)

    # Test concurrent functionality of module
    def test_yf_concurrency(self):
        # Multi stock test
        multi_balance_sheet_data_qt = self.test_yf_concurrent.get_financial_stmts('quarterly', 'balance')
        multi_income_statement_data_qt = self.test_yf_concurrent.get_financial_stmts('quarterly', 'income')
        multi_all_statement_data_qt = self.test_yf_concurrent.get_financial_stmts('quarterly',
                                                                                  ['income', 'cash', 'balance'])
        # Multi stock check
        result = check_fundamental(multi_balance_sheet_data_qt, 'bal')
        self.assertEqual(result, True)
        result = check_fundamental(multi_income_statement_data_qt, 'inc')
        self.assertEqual(result, True)
        result = check_fundamental(multi_all_statement_data_qt, 'all')
        self.assertEqual(result, True)

    # Extra Module Methods Test
    def test_yf_module_methods(self):

        # 10 Day Average Daily Volume
        if isinstance(self.test_yf_stock_single.get_ten_day_avg_daily_volume(), int):
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)
        
        # Stock Current Price
        if isinstance(self.test_yf_stock_single.get_current_price(), float):
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)
        # Stock Net Income
        if isinstance(self.test_yf_stock_single.get_net_income(), float):
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Stock Financial Data
        if self.test_yf_stock_single.get_financial_data().get("C").get("financialCurrency") == "USD":
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Stock Profile Data
        if self.test_yf_stock_single.get_stock_profile_data().get("C").get("sector") == "Financial Services":
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Stock Summary Data
        if self.test_yf_stock_single.get_summary_data().get("C").get("currency") == "USD":
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Stock Price Data
        if self.test_yf_stock_single.get_stock_price_data().get("C").get("exchangeName") == "NYSE":
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Stock Key Statistics
        if isinstance(self.test_yf_stock_single.get_key_statistics_data().get("C").get("forwardPE"), float):
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Stock ESG SCORES
        if self.test_yf_stock_single.get_esg_score_data().get("C").get("peerGroup") == "Banks":
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)

        # Treasuries
        if isinstance(self.test_yf_treasuries_single.get_current_price(), float):
            self.assertEqual(True, True)
        else:
            self.assertEqual(False, True)


if __name__ == "__main__":
    t_main()
