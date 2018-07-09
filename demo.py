#!/usr/bin/python

from __future__ import print_function
from yahoofinancials import YahooFinancials as YF

def doit(ticker):
    mark = '-' * 64
    tick = YF(ticker)
    print(mark)
    print(tick.get_stock_summary_data())
    print(mark)
    print(tick.get_stock_quote_type_data())
    print(mark)
    print(tick.get_stock_price_data())
    print(mark)
    print(tick.get_current_price())
    print(mark)
    print(tick.get_dividend_rate())
    print(mark)
    try:
        print(tick._cache.keys())
        print(mark)
    except AttributeError:
        pass



if __name__ == '__main__':
    import sys
    import time
    ts = sys.argv[1:] or ['MMM', 'AAPL']
    st = time.time()
    doit(ts[0] if 1 == len(ts) else ts)
    print(time.time() - st, 'seconds')
