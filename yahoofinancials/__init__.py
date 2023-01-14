from multiprocessing import freeze_support, set_start_method


if __name__ == '__main__':
    freeze_support()
    set_start_method("spawn")
    from yahoofinancials.yf import YahooFinancials
else:
    from yahoofinancials.yf import YahooFinancials
