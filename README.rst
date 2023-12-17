===============
yahoofinancials
===============

A python module that returns stock, cryptocurrency, forex, mutual fund, commodity futures, ETF, and US Treasury financial data from Yahoo Finance.

.. image:: https://github.com/JECSand/yahoofinancials/actions/workflows/test.yml/badge.svg?branch=master
    :target: https://github.com/JECSand/yahoofinancials/actions/workflows/test.yml

.. image:: https://static.pepy.tech/badge/yahoofinancials
    :target: https://pepy.tech/project/yahoofinancials

.. image:: https://static.pepy.tech/badge/yahoofinancials/month
    :target: https://pepy.tech/project/yahoofinancials

.. image:: https://static.pepy.tech/badge/yahoofinancials/week
    :target: https://pepy.tech/project/yahoofinancials

Current Version: v1.20

Version Released: 12/17/2023

Report any bugs by opening an issue here: https://github.com/JECSand/yahoofinancials/issues

Overview
--------
A powerful financial data module used for pulling both fundamental and technical data from Yahoo Finance.

- New analytic methods in v1.20:
    - get_insights()
        - returns data for:
            - 'instrumentInfo'
            - 'companySnapshot'
            - 'recommendation'
            - 'sigDevs'
            - 'secReports'
    - get_recommendations()

- Example:

.. code-block:: python

    print(YahooFinancials('C').get_recommendations())

- Example Output:

.. code-block:: javascript

    {
        "C": [
            {
                "recommendedSymbols": [
                    {
                        "score": 0.239602,
                        "symbol": "BAC"
                    },
                    {
                    "score": 0.225134,
                    "symbol": "JPM"
                    },
                    {
                    "score": 0.167669,
                    "symbol": "WFC"
                    },
                    {
                    "score": 0.145864,
                    "symbol": "GS"
                    },
                    {
                    "score": 0.134071,
                    "symbol": "F"
                    }
                ],
                "symbol": "C"
            }
        ]
    }

- As of Version 1.20, YahooFinancials supports a new optional parameter called flat_format.
    - When `YahooFinancials(flat_format=True)`, financial statement data will return in a dict instead of a list. The keys of the dict will be the reporting dates.
    - Default is False, to ensure backwards compatibility.


- As of Version 1.9, YahooFinancials supports optional parameters for asynchronous execution, proxies, and international requests.

.. code-block:: python

    from yahoofinancials import YahooFinancials
    tickers = ['AAPL', 'GOOG', 'C']
    yahoo_financials = YahooFinancials(tickers, concurrent=True, max_workers=8, country="US")
    balance_sheet_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'balance')
    print(balance_sheet_data_qt)

    proxy_addresses = [ "mysuperproxy.com:5000", "mysuperproxy.com:5001"]
    yahoo_financials = YahooFinancials(tickers, concurrent=True, proxies=proxy_addresses)
    balance_sheet_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'balance')
    print(balance_sheet_data_qt)

Installation
-------------
- yahoofinancials runs on Python 3.7, 3.8, 3.9, 3.10, 3.11, and 3.12

1. Installation using pip:

- Linux/Mac:

.. code-block:: bash

    $ pip install yahoofinancials

- Windows (If python doesn't work for you in cmd, try running the following command with just py):

.. code-block::

    > python -m pip install yahoofinancials

2. Installation using github (Mac/Linux):

.. code-block:: bash

    $ git clone https://github.com/JECSand/yahoofinancials.git
    $ cd yahoofinancials
    $ python setup.py install

3. Demo using the included demo script:

.. code-block:: bash

    $ cd yahoofinancials
    $ python demo.py -h
    $ python demo.py
    $ python demo.py WFC C BAC

4. Test using the included unit testing script:

.. code-block:: bash

    $ cd yahoofinancials
    $ python test/test_yahoofinancials.py

Module Methods
--------------
- The financial data from all methods is returned as JSON.
- You can run multiple symbols at once using an inputted array or run an individual symbol using an inputted string.
- YahooFinancials works with Python 3.7, 3.8, 3.9, 3.10, 3.11 and 3.12 and runs on all operating systems. (Windows, Mac, Linux).

Featured Methods
^^^^^^^^^^^^^^^^
1. get_financial_stmts(frequency, statement_type, reformat=True)

   - frequency can be either 'annual' or 'quarterly'.
   - statement_type can be 'income', 'balance', 'cash' or a list of several.
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
2. get_stock_price_data(reformat=True)

3. get_stock_earnings_data()

   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
4. get_summary_data(reformat=True)

   - Returns financial summary data for cryptocurrencies, stocks, currencies, ETFs, mutual funds, U.S. Treasuries, commodity futures, and indexes.
   - reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
5. get_stock_quote_type_data()

6. get_historical_price_data(start_date, end_date, time_interval)

   - This method will pull historical pricing data for stocks, currencies, ETFs, mutual funds, U.S. Treasuries, cryptocurrencies, commodities, and indexes.
   - start_date should be entered in the 'YYYY-MM-DD' format and is the first day that data will be pulled for.
   - end_date should be entered in the 'YYYY-MM-DD' format and is the last day that data will be pulled for.
   - time_interval can be either 'daily', 'weekly', or 'monthly'. This variable determines the time period interval for your pull.
   - Data response includes relevant pricing event data such as dividends and stock splits.
7. get_num_shares_outstanding(price_type='current')

   - price_type can also be set to 'average' to calculate the shares outstanding with the daily average price.

Additional Module Methods
^^^^^^^^^^^^^^^^^^^^^^^^^
- get_daily_dividend_data(start_date, end_date)
- get_stock_profile_data()
- get_financial_data()
- get_interest_expense()
- get_operating_income()
- get_total_operating_expense()
- get_total_revenue()
- get_cost_of_revenue()
- get_income_before_tax()
- get_income_tax_expense()
- get_esg_score_data()
- get_gross_profit()
- get_net_income_from_continuing_ops()
- get_research_and_development()
- get_current_price()
- get_current_change()
- get_current_percent_change()
- get_current_volume()
- get_prev_close_price()
- get_open_price()
- get_ten_day_avg_daily_volume()
- get_stock_exchange()
- get_market_cap()
- get_daily_low()
- get_daily_high()
- get_currency()
- get_yearly_high()
- get_yearly_low()
- get_dividend_yield()
- get_annual_avg_div_yield()
- get_five_yr_avg_div_yield()
- get_dividend_rate()
- get_annual_avg_div_rate()
- get_50day_moving_avg()
- get_200day_moving_avg()
- get_beta()
- get_payout_ratio()
- get_pe_ratio()
- get_price_to_sales()
- get_exdividend_date()
- get_book_value()
- get_ebit()
- get_net_income()
- get_earnings_per_share()
- get_key_statistics_data()
- get_stock_profile_data()
- get_financial_data()

Usage Examples
--------------
- The class constructor can take either a single ticker or a list of tickers as it's parameter.
- This makes it easy to initiate multiple classes for different groupings of financial assets.
- Quarterly statement data returns the last 4 periods of data, while annual returns the last 3.

Single Ticker Example
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from yahoofinancials import YahooFinancials

    ticker = 'AAPL'
    yahoo_financials = YahooFinancials(ticker)

    balance_sheet_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'balance')
    income_statement_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'income')
    all_statement_data_qt =  yahoo_financials.get_financial_stmts('quarterly', ['income', 'cash', 'balance'])
    apple_earnings_data = yahoo_financials.get_stock_earnings_data()
    apple_net_income = yahoo_financials.get_net_income()
    historical_stock_prices = yahoo_financials.get_historical_price_data('2008-09-15', '2018-09-15', 'weekly')

Lists of Tickers Example
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from yahoofinancials import YahooFinancials

    tech_stocks = ['AAPL', 'MSFT', 'INTC']
    bank_stocks = ['WFC', 'BAC', 'C']
    commodity_futures = ['GC=F', 'SI=F', 'CL=F']
    cryptocurrencies = ['BTC-USD', 'ETH-USD', 'XRP-USD']
    currencies = ['EURUSD=X', 'JPY=X', 'GBPUSD=X']
    mutual_funds = ['PRLAX', 'QASGX', 'HISFX']
    us_treasuries = ['^TNX', '^IRX', '^TYX']

    yahoo_financials_tech = YahooFinancials(tech_stocks)
    yahoo_financials_banks = YahooFinancials(bank_stocks)
    yahoo_financials_commodities = YahooFinancials(commodity_futures)
    yahoo_financials_cryptocurrencies = YahooFinancials(cryptocurrencies)
    yahoo_financials_currencies = YahooFinancials(currencies)
    yahoo_financials_mutualfunds = YahooFinancials(mutual_funds)
    yahoo_financials_treasuries = YahooFinancials(us_treasuries)

    tech_cash_flow_data_an = yahoo_financials_tech.get_financial_stmts('annual', 'cash')
    bank_cash_flow_data_an = yahoo_financials_banks.get_financial_stmts('annual', 'cash')

    banks_net_ebit = yahoo_financials_banks.get_ebit()
    tech_stock_price_data = yahoo_financials_tech.get_stock_price_data()
    daily_bank_stock_prices = yahoo_financials_banks.get_historical_price_data('2008-09-15', '2018-09-15', 'daily')
    daily_commodity_prices = yahoo_financials_commodities.get_historical_price_data('2008-09-15', '2018-09-15', 'daily')
    daily_crypto_prices = yahoo_financials_cryptocurrencies.get_historical_price_data('2008-09-15', '2018-09-15', 'daily')
    daily_currency_prices = yahoo_financials_currencies.get_historical_price_data('2008-09-15', '2018-09-15', 'daily')
    daily_mutualfund_prices = yahoo_financials_mutualfunds.get_historical_price_data('2008-09-15', '2018-09-15', 'daily')
    daily_treasury_prices = yahoo_financials_treasuries.get_historical_price_data('2008-09-15', '2018-09-15', 'daily')

Examples of Returned JSON Data
------------------------------

1. Annual Income Statement Data for Apple:


.. code-block:: python

    yahoo_financials = YahooFinancials('AAPL')
    print(yahoo_financials.get_financial_stmts('annual', 'income'))


.. code-block:: javascript

    {
        "incomeStatementHistory": {
            "AAPL": [
                {
                    "2016-09-24": {
                        "minorityInterest": null,
                        "otherOperatingExpenses": null,
                        "netIncomeFromContinuingOps": 45687000000,
                        "totalRevenue": 215639000000,
                        "totalOtherIncomeExpenseNet": 1348000000,
                        "discontinuedOperations": null,
                        "incomeTaxExpense": 15685000000,
                        "extraordinaryItems": null,
                        "grossProfit": 84263000000,
                        "netIncome": 45687000000,
                        "sellingGeneralAdministrative": 14194000000,
                        "interestExpense": null,
                        "costOfRevenue": 131376000000,
                        "researchDevelopment": 10045000000,
                        "netIncomeApplicableToCommonShares": 45687000000,
                        "effectOfAccountingCharges": null,
                        "incomeBeforeTax": 61372000000,
                        "otherItems": null,
                        "operatingIncome": 60024000000,
                        "ebit": 61372000000,
                        "nonRecurring": null,
                        "totalOperatingExpenses": 0
                    }
                }
            ]
        }
    }

2. Annual Balance Sheet Data for Apple:


.. code-block:: python

    yahoo_financials = YahooFinancials('AAPL')
    print(yahoo_financials.get_financial_stmts('annual', 'balance'))


.. code-block:: javascript

    {
        "balanceSheetHistory": {
            "AAPL": [
                {
                    "2016-09-24": {
                        "otherCurrentLiab": 8080000000,
                        "otherCurrentAssets": 8283000000,
                        "goodWill": 5414000000,
                        "shortTermInvestments": 46671000000,
                        "longTermInvestments": 170430000000,
                        "cash": 20484000000,
                        "netTangibleAssets": 119629000000,
                        "totalAssets": 321686000000,
                        "otherLiab": 36074000000,
                        "totalStockholderEquity": 128249000000,
                        "inventory": 2132000000,
                        "retainedEarnings": 96364000000,
                        "intangibleAssets": 3206000000,
                        "totalCurrentAssets": 106869000000,
                        "otherStockholderEquity": 634000000,
                        "shortLongTermDebt": 11605000000,
                        "propertyPlantEquipment": 27010000000,
                        "deferredLongTermLiab": 2930000000,
                        "netReceivables": 29299000000,
                        "otherAssets": 8757000000,
                        "longTermDebt": 75427000000,
                        "totalLiab": 193437000000,
                        "commonStock": 31251000000,
                        "accountsPayable": 59321000000,
                        "totalCurrentLiabilities": 79006000000
                    }
                }
            ]
        }
    }

3. Quarterly Cash Flow Statement Data for Citigroup:


.. code-block:: python

    yahoo_financials = YahooFinancials('C')
    print(yahoo_financials.get_financial_stmts('quarterly', 'cash'))


.. code-block:: javascript

    {
        "cashflowStatementHistoryQuarterly": {
            "C": [
                {
                    "2017-06-30": {
                        "totalCashFromOperatingActivities": -18505000000,
                        "effectOfExchangeRate": -117000000,
                        "totalCashFromFinancingActivities": 39798000000,
                        "netIncome": 3872000000,
                        "dividendsPaid": -760000000,
                        "salePurchaseOfStock": -1781000000,
                        "capitalExpenditures": -861000000,
                        "changeToLiabilities": -7626000000,
                        "otherCashflowsFromInvestingActivities": 82000000,
                        "totalCashflowsFromInvestingActivities": -22508000000,
                        "netBorrowings": 33586000000,
                        "depreciation": 901000000,
                        "changeInCash": -1332000000,
                        "changeToNetincome": 1444000000,
                        "otherCashflowsFromFinancingActivities": 8753000000,
                        "changeToOperatingActivities": -17096000000,
                        "investments": -23224000000
                    }
                }
            ]
        }
    }

4. Monthly Historical Stock Price Data for Wells Fargo:


.. code-block:: python

    yahoo_financials = YahooFinancials('WFC')
    print(yahoo_financials.get_historical_price_data("2018-07-10", "2018-08-10", "monthly"))


.. code-block:: javascript

    {
        "WFC": {
            "currency": "USD",
            "eventsData": {
                "dividends": {
                    "2018-08-01": {
                        "amount": 0.43,
                        "date": 1533821400,
                        "formatted_date": "2018-08-09"
                    }
                }
            },
            "firstTradeDate": {
                "date": 76233600,
                "formatted_date": "1972-06-01"
            },
            "instrumentType": "EQUITY",
            "prices": [
                {
                    "adjclose": 57.19147872924805,
                    "close": 57.61000061035156,
                    "date": 1533096000,
                    "formatted_date": "2018-08-01",
                    "high": 59.5,
                    "low": 57.08000183105469,
                    "open": 57.959999084472656,
                    "volume": 138922900
                }
            ],
            "timeZone": {
                "gmtOffset": -14400
            }
        }
    }

5. Monthly Historical Price Data for EURUSD:


.. code-block:: python

    yahoo_financials = YahooFinancials('EURUSD=X')
    print(yahoo_financials.get_historical_price_data("2018-07-10", "2018-08-10", "monthly"))


.. code-block:: javascript

    {
        "EURUSD=X": {
            "currency": "USD",
            "eventsData": {},
            "firstTradeDate": {
                "date": 1070236800,
                "formatted_date": "2003-12-01"
            },
            "instrumentType": "CURRENCY",
            "prices": [
                {
                    "adjclose": 1.1394712924957275,
                    "close": 1.1394712924957275,
                    "date": 1533078000,
                    "formatted_date": "2018-07-31",
                    "high": 1.169864296913147,
                    "low": 1.1365960836410522,
                    "open": 1.168961763381958,
                    "volume": 0
                }
            ],
            "timeZone": {
                "gmtOffset": 3600
            }
        }
    }

6. Monthly Historical Price Data for BTC-USD:


.. code-block:: python

    yahoo_financials = YahooFinancials('BTC-USD')
    print(yahoo_financials.get_historical_price_data("2018-07-10", "2018-08-10", "monthly"))


.. code-block:: javascript

    {
        "BTC-USD": {
            "currency": "USD",
            "eventsData": {},
            "firstTradeDate": {
                "date": 1279321200,
                "formatted_date": "2010-07-16"
            },
            "instrumentType": "CRYPTOCURRENCY",
            "prices": [
                {
                    "adjclose": 6285.02001953125,
                    "close": 6285.02001953125,
                    "date": 1533078000,
                    "formatted_date": "2018-07-31",
                    "high": 7760.740234375,
                    "low": 6133.02978515625,
                    "open": 7736.25,
                    "volume": 4334347882
                }
            ],
            "timeZone": {
                "gmtOffset": 3600
            }
        }
    }

7. Weekly Historical Price Data for Crude Oil Futures:


.. code-block:: python

    yahoo_financials = YahooFinancials('CL=F')
    print(yahoo_financials.get_historical_price_data("2018-08-01", "2018-08-10", "weekly"))


.. code-block:: javascript

    {
        "CL=F": {
            "currency": "USD",
            "eventsData": {},
            "firstTradeDate": {
                "date": 1522555200,
                "formatted_date": "2018-04-01"
            },
            "instrumentType": "FUTURE",
            "prices": [
                {
                    "adjclose": 68.58999633789062,
                    "close": 68.58999633789062,
                    "date": 1532923200,
                    "formatted_date": "2018-07-30",
                    "high": 69.3499984741211,
                    "low": 66.91999816894531,
                    "open": 68.37000274658203,
                    "volume": 683048039
                },
                {
                    "adjclose": 67.75,
                    "close": 67.75,
                    "date": 1533528000,
                    "formatted_date": "2018-08-06",
                    "high": 69.91999816894531,
                    "low": 66.13999938964844,
                    "open": 68.76000213623047,
                    "volume": 1102357981
                }
            ],
            "timeZone": {
                "gmtOffset": -14400
            }
        }
    }

8. Apple Stock Quote Data:


.. code-block:: python

    yahoo_financials = YahooFinancials('AAPL')
    print(yahoo_financials.get_stock_quote_type_data())


.. code-block:: javascript

    {
        "AAPL": {
            "underlyingExchangeSymbol": null,
            "exchangeTimezoneName": "America/New_York",
            "underlyingSymbol": null,
            "headSymbol": null,
            "shortName": "Apple Inc.",
            "symbol": "AAPL",
            "uuid": "8b10e4ae-9eeb-3684-921a-9ab27e4d87aa",
            "gmtOffSetMilliseconds": "-14400000",
            "exchange": "NMS",
            "exchangeTimezoneShortName": "EDT",
            "messageBoardId": "finmb_24937",
            "longName": "Apple Inc.",
            "market": "us_market",
            "quoteType": "EQUITY"
        }
    }

9. U.S. Treasury Current Pricing Data:


.. code-block:: python

    yahoo_financials = YahooFinancials(['^TNX', '^IRX', '^TYX'])
    print(yahoo_financials.get_current_price())


.. code-block:: javascript

    {
        "^IRX": 2.033,
        "^TNX": 2.895,
        "^TYX": 3.062
    }

10. BTC-USD Summary Data:


.. code-block:: python

    yahoo_financials = YahooFinancials('BTC-USD')
    print(yahoo_financials.get_summary_data())


.. code-block:: javascript

    {
        "BTC-USD": {
            "algorithm": "SHA256",
            "ask": null,
            "askSize": null,
            "averageDailyVolume10Day": 545573809,
            "averageVolume": 496761640,
            "averageVolume10days": 545573809,
            "beta": null,
            "bid": null,
            "bidSize": null,
            "circulatingSupply": 17209812,
            "currency": "USD",
            "dayHigh": 6266.5,
            "dayLow": 5891.87,
            "dividendRate": null,
            "dividendYield": null,
            "exDividendDate": "-",
            "expireDate": "-",
            "fiftyDayAverage": 6989.074,
            "fiftyTwoWeekHigh": 19870.62,
            "fiftyTwoWeekLow": 2979.88,
            "fiveYearAvgDividendYield": null,
            "forwardPE": null,
            "fromCurrency": "BTC",
            "lastMarket": "CCCAGG",
            "marketCap": 106325663744,
            "maxAge": 1,
            "maxSupply": 21000000,
            "navPrice": null,
            "open": 6263.2,
            "openInterest": null,
            "payoutRatio": null,
            "previousClose": 6263.2,
            "priceHint": 2,
            "priceToSalesTrailing12Months": null,
            "regularMarketDayHigh": 6266.5,
            "regularMarketDayLow": 5891.87,
            "regularMarketOpen": 6263.2,
            "regularMarketPreviousClose": 6263.2,
            "regularMarketVolume": 755834368,
            "startDate": "2009-01-03",
            "strikePrice": null,
            "totalAssets": null,
            "tradeable": false,
            "trailingAnnualDividendRate": null,
            "trailingAnnualDividendYield": null,
            "twoHundredDayAverage": 8165.154,
            "volume": 755834368,
            "volume24Hr": 750196480,
            "volumeAllCurrencies": 2673437184,
            "yield": null,
            "ytdReturn": null
        }
    }

11. Apple Key Statistics Data:


.. code-block:: python

    yahoo_financials = YahooFinancials('AAPL')
    print(yahoo_financials.get_key_statistics_data())


.. code-block:: javascript

    {
        "AAPL": {
            "annualHoldingsTurnover": null,
            "enterpriseToRevenue": 2.973,
            "beta3Year": null,
            "profitMargins": 0.22413999,
            "enterpriseToEbitda": 9.652,
            "52WeekChange": -0.12707871,
            "morningStarRiskRating": null,
            "forwardEps": 13.49,
            "revenueQuarterlyGrowth": null,
            "sharesOutstanding": 4729800192,
            "fundInceptionDate": "-",
            "annualReportExpenseRatio": null,
            "totalAssets": null,
            "bookValue": 22.534,
            "sharesShort": 44915125,
            "sharesPercentSharesOut": 0.0095,
            "fundFamily": null,
            "lastFiscalYearEnd": 1538179200,
            "heldPercentInstitutions": 0.61208,
            "netIncomeToCommon": 59531001856,
            "trailingEps": 11.91,
            "lastDividendValue": null,
            "SandP52WeekChange": -0.06475246,
            "priceToBook": 6.7582316,
            "heldPercentInsiders": 0.00072999997,
            "nextFiscalYearEnd": 1601337600,
            "yield": null,
            "mostRecentQuarter": 1538179200,
            "shortRatio": 1,
            "sharesShortPreviousMonthDate": "2018-10-31",
            "floatShares": 4489763410,
            "beta": 1.127094,
            "enterpriseValue": 789555511296,
            "priceHint": 2,
            "threeYearAverageReturn": null,
            "lastSplitDate": "2014-06-09",
            "lastSplitFactor": "1/7",
            "legalType": null,
            "morningStarOverallRating": null,
            "earningsQuarterlyGrowth": 0.318,
            "priceToSalesTrailing12Months": null,
            "dateShortInterest": 1543536000,
            "pegRatio": 0.98,
            "ytdReturn": null,
            "forwardPE": 11.289103,
            "maxAge": 1,
            "lastCapGain": null,
            "shortPercentOfFloat": 0.0088,
            "sharesShortPriorMonth": 36469092,
            "category": null,
            "fiveYearAverageReturn": null
        }
    }

12. Apple and Wells Fargo Daily Dividend Data:


.. code-block:: python

    start_date = '1987-09-15'
    end_date = '1988-09-15'
    yahoo_financials = YahooFinancials(['AAPL', 'WFC'])
    print(yahoo_financials.get_daily_dividend_data(start_date, end_date))


.. code-block:: javascript

    {
        "AAPL": [
            {
                "date": 564157800,
                "formatted_date": "1987-11-17",
                "amount": 0.08
            },
            {
                "date": 571674600,
                "formatted_date": "1988-02-12",
                "amount": 0.08
            },
            {
                "date": 579792600,
                "formatted_date": "1988-05-16",
                "amount": 0.08
            },
            {
                "date": 587655000,
                "formatted_date": "1988-08-15",
                "amount": 0.08
            }
        ],
        "WFC": [
            {
                "date": 562861800,
                "formatted_date": "1987-11-02",
                "amount": 0.3008
            },
            {
                "date": 570724200,
                "formatted_date": "1988-02-01",
                "amount": 0.3008
            },
            {
                "date": 578583000,
                "formatted_date": "1988-05-02",
                "amount": 0.3344
            },
            {
                "date": 586445400,
                "formatted_date": "1988-08-01",
                "amount": 0.3344
            }
        ]
    }

13. Apple key Financial Data:


.. code-block:: python

    yahoo_financials = YahooFinancials("AAPL")
    print(yahoo_financials.get_financial_data())


.. code-block:: javascript

    {
        'AAPL': {
            'ebitdaMargins': 0.29395,
            'profitMargins': 0.21238,
            'grossMargins': 0.37818,
            'operatingCashflow': 69390999552,
            'revenueGrowth': 0.018,
            'operatingMargins': 0.24572,
            'ebitda': 76476997632,
            'targetLowPrice': 150,
            'recommendationKey': 'buy',
            'grossProfits': 98392000000,
            'freeCashflow': 42914250752,
            'targetMedianPrice': 270,
            'currentPrice': 261.78,
            'earningsGrowth': 0.039,
            'currentRatio': 1.54,
            'returnOnAssets': 0.11347,
            'numberOfAnalystOpinions': 40,
            'targetMeanPrice': 255.51,
            'debtToEquity': 119.405,
            'returnOnEquity': 0.55917,
            'targetHighPrice': 300,
            'totalCash': 100556996608,
            'totalDebt': 108046999552,
            'totalRevenue': 260174004224,
            'totalCashPerShare': 22.631,
            'financialCurrency': 'USD',
            'maxAge': 86400,
            'revenuePerShare': 56.341,
            'quickRatio': 1.384,
            'recommendationMean': 2.2
        }
    }
