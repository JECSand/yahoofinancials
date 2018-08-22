#!/usr/bin/python

"""
%(scriptname)s [-h|--help] [api [api [...]]] [ticker [ticker [...]]]
    no args: show some information about default tickers (%(defaultargs)s)
    ticker(s): show some information about specified ticker(s)
    api name(s) and ticker(s): show the specified api(s) result for the ticker(s)
    yf and -h: show apis
    api name(s) and -h: show help for that api
    -h or --help: show usage
"""

from __future__ import print_function
import sys
import time
from yahoofinancials import YahooFinancials as YF


DEFAULT_ARGS = ('MMM', 'AAPL')
MODULE_ARGS = ('yf', 'yahoofinancial', 'yahoofinancials')
HELP_ARGS = ('-h', '--help')

mark = '-' * 64


def defaultapi(ticker):
    tick = YF(ticker)
    print(tick.get_summary_data())
    print(mark)
    print(tick.get_stock_quote_type_data())
    print(mark)
    print(tick.get_stock_price_data())
    print(mark)
    print(tick.get_current_price())
    print(mark)
    print(tick.get_dividend_rate())
    try:
        r = tick._cache.keys()
    except AttributeError:
        pass
    else:
        print(mark)
        print(r)


def customapi(queries, ts):
    yf = YF(ts[0] if 1 == len(ts) else ts)
    for q in queries:
        print('%s:' % (q,))
        timeit(lambda: print(getattr(yf, q)()))


def helpapi(queries):
    if len(queries) == 1:
        print(__doc__ % {'scriptname': sys.argv[0], 'defaultargs': ', '.join(DEFAULT_ARGS)})
    else:
        import pydoc
        for q in queries:
            if q in MODULE_ARGS:
                print(pydoc.render_doc(YF, "Help on %s"))
            elif q not in HELP_ARGS:
                print(pydoc.render_doc(getattr(YF, q), "Help on %s"))


def timeit(f, *args):
    print(mark)
    st = time.time()
    f(*args)
    et = time.time()
    print(mark)
    print(et - st, 'seconds')



if __name__ == '__main__':
    api = set(s for s in dir(YF) if s.startswith('get_'))
    api.update(MODULE_ARGS)
    api.update(HELP_ARGS)
    ts = sys.argv[1:]
    queries = [q for q in ts if q in api]
    ts = [t for t in ts if not t in queries] or DEFAULT_ARGS
    if [h for h in HELP_ARGS if h in queries]:
        helpapi(queries)
    elif queries:
        customapi(queries, ts)
    else:
        timeit(defaultapi, ts[0] if 1 == len(ts) else ts)
