def eps(price_data, pe_ratio):
    if price_data is not None and pe_ratio is not None:
        return price_data / pe_ratio
    else:
        return None


def num_shares_outstanding(cur_market_cap, today_low, today_high, price_type, current):
    if cur_market_cap is not None:
        if price_type == 'current':
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
