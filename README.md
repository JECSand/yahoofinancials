# yahoofinancials
Welcome to Yahoo Financials!

Current Version: v0.7

Version Released: 08/03/2018


New Contributers Welcomed!

Email sandersconnor1@gmail.com with YAHOOFINANCIALS-{Your-Name} as email title if interested.

## Overview
A powerful financial data module used for pulling both fundamental and technical stock data from Yahoo Finance.
The module uses a web scraping technique for retrieving the data, thus eliminating the need for the now discontinued Yahoo Finance API.

## Installation
* yahoofinancials runs fine on most versions of python 2 and 3.
* It was built and tested using versions 2.7 and 3.4
* the package depends on beautifulsoup4 and requests to work

1. Installation using pip:
* Linux/Mac:
```R
$ pip install yahoofinancials
```
* Windows (If python doesn't work for you in cmd, try running the following command with just py):
```R
> python -m pip install yahoofinancials
```
2. Installation using github (Mac/Linux):
```R
$ git clone https://github.com/JECSand/yahoofinancials.git
$ cd yahoofinancials
$ python setup.py install
```
3. Demo using the included demo script:
```R
$ cd yahoofinancials
$ python demo.py -h
$ python demo.py
$ python demo.py WFC C BAC
```

## Module Methods
* The financial data from all methods is returned as JSON.
* You can run multiple stocks at once using an inputted array or run an individual stock using an inputted string.
* YahooFinancials works on most versions of python 2 and 3 and runs on all operating systems. (Windows, Mac, Linux)

### Featured Methods
1. get_financial_stmts(frequency, statement_type, reformat=True)
   * frequency can be either 'annual' or 'quarterly'.
   * statement_type can be 'income', 'balance', 'cash' or a list of several.
   * reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
2. get_stock_price_data(reformat=True)
   * reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
3. get_stock_earnings_data(reformat=True)
   * reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
4. get_stock_summary_data(reformat=True)
   * reformat optional value defaulted to true. Enter False for unprocessed raw data from Yahoo Finance.
5. get_stock_quote_type_data()
6. get_historical_stock_data(start_date, end_date, time_interval)
   * start_date should be entered in the 'YYYY-MM-DD' format. First day that stock data will be pulled.
   * end_date should be entered in the 'YYYY-MM-DD' format. Last day that stock data will be pulled.
   * time_interval can be either 'daily', 'weekly', or 'monthly'. Parameter determines the time period interval.

### 10 New Module Methods Added in v0.7
* get_interest_expense():
* get_operating_income():
* get_total_operating_expense():
* get_total_revenue():
* get_cost_of_revenue():
* get_income_before_tax():
* get_income_tax_expense():
* get_gross_profit():
* get_net_income_from_continuing_ops():
* get_research_and_development():

### Additional Module Methods
* get_current_price():
* get_current_change():
* get_current_percent_change():
* get_current_volume():
* get_prev_close_price():
* get_open_price():
* get_ten_day_avg_daily_volume():
* get_three_month_avg_daily_volume():
* get_stock_exchange():
* get_market_cap():
* get_daily_low():
* get_daily_high():
* get_currency():
* get_yearly_high():
* get_yearly_low():
* get_dividend_yield():
* get_annual_avg_div_yield():
* get_five_yr_avg_div_yield():
* get_dividend_rate():
* get_annual_avg_div_rate():
* get_50day_moving_avg():
* get_200day_moving_avg():
* get_beta():
* get_payout_ratio():
* get_pe_ratio():
* get_price_to_sales():
* get_exdividend_date():
* get_book_value():
* get_ebit():
* get_net_income():
* get_earnings_per_share():

## Usage Examples
* The class constructor can take either a single ticker or a list of tickers as it's parameter.
* This makes it easy to construct multiple classes for different groupings of stocks
* Quarterly statement data returns the last 4 periods of data, while annual returns the past 3.

### Single Ticker Example
```R
from yahoofinancials import YahooFinancials

ticker = 'AAPL'
yahoo_financials = YahooFinancials(ticker)

balance_sheet_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'balance')
income_statement_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'income')
all_statement_data_qt =  yahoo_financials.get_financial_stmts('quarterly', ['income', 'cash', 'balance'])
apple_earnings_data = yahoo_financials.get_stock_earnings_data()
apple_net_income = yahoo_financials.get_net_income()
historical_stock_prices = yahoo_financials.get_historical_stock_data('2015-01-15', '2017-10-15', 'weekly')
```

### Lists of Tickers Example
```R
from yahoofinancials import YahooFinancials

tech_stocks = ['AAPL', 'MSFT', 'INTC']
bank_stocks = ['WFC', 'BAC', 'C']

yahoo_financials_tech = YahooFinancials(tech_stocks)
yahoo_financials_banks = YahooFinancials(bank_stocks)

tech_cash_flow_data_an = yahoo_financials_tech.get_financial_stmts('annual', 'cash')
bank_cash_flow_data_an = yahoo_financials_banks.get_financial_stmts('annual', 'cash')

banks_net_ebit = yahoo_financials_banks.get_ebit()
tech_stock_price_data = tech_cash_flow_data.get_stock_price_data()
daily_bank_stock_prices = yahoo_financials_banks.get_historical_stock_data('2008-09-15', '2017-09-15', 'daily')
```

## Examples of Returned JSON Data
1. Annual Income Statement Data for Apple:
```R
yahoo_financials = YahooFinancials('AAPL')
print(yahoo_financials.get_financial_stmts('annual', 'income'))
```
```javascript
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
```
2. Annual Balance Sheet Data for Apple:
```R
yahoo_financials = YahooFinancials('AAPL')
print(yahoo_financials.get_financial_stmts('annual', 'balance'))
```
```javascript
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
```
3. Quarterly Cash Flow Statement Data for Citigroup:
```R
yahoo_financials = YahooFinancials('C')
print(yahoo_financials.get_financial_stmts('quarterly', 'cash'))
```
```javascript
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
```
4. Monthly Stock Price History Data for Wells Fargo:
```R
yahoo_financials = YahooFinancials('WFC')
print(yahoo_financials.get_historical_stock_data("2017-09-10", "2017-10-10", "monthly"))
```
```javascript
{
    "WFC": {
        "prices": [
            {
                "volume": 260271600,
                "formatted_date": "2017-09-30",
                "high": 55.77000045776367,
                "adjclose": 54.91999816894531,
                "low": 52.84000015258789,
                "date": 1506830400,
                "close": 54.91999816894531,
                "open": 55.15999984741211
            }
        ],
        "eventsData": [],
        "firstTradeDate": {
            "date": 76233600,
            "formatted_date": "1972-06-01"
        },
        "isPending": false,
        "timeZone": {
            "gmtOffset": -14400
        },
        "id": "1mo15050196001507611600"
    }
}
```
5. Apple Stock Quote Data:
```R
yahoo_financials = YahooFinancials('AAPL')
print(yahoo_financials.get_stock_quote_type_data())
```
```javascript
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
```
