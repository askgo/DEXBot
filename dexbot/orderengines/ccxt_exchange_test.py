import logging
import os
import configparser

import ccxt
from ccxt_exchange import CcxtExchange
from ccxt_engine import CcxtOrderEngine

"""
    Temporary informal unit test for ccxt exchange
"""

# update this to reflect your config file
config_file = "ccxt_config/secrets_test.ini"


if __name__ == '__main__':

    log = logging.getLogger(__name__)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    symbol = 'BTC/USDT'
    log.info("symbol: {} ".format(symbol))


    config_dir = os.path.dirname(__file__)
    parser = configparser.ConfigParser()
    parser.read(os.path.join(config_dir, config_file))
    exch_ids = parser.sections()
    
    sec = {section_name: dict(parser.items(section_name)) for section_name in exch_ids}

    # need to fix below in order to check for for acceptable exchanges and parameters

    # for now, get 0th exchange
    exch_name = list(sec)[0]
    apikey = sec[exch_name]['api_key']
    secret = sec[exch_name]['secret']
    log.info(apikey)
    log.info(secret)

    # coin tiger requires an API key, even if only for ticker data
    ccxt_ex = getattr(ccxt, exch_name)({
        "apiKey": apikey,
        "secret": secret,
        'timeout': 30000,
        'enableRateLimit': True,
        'verbose': False,
    })

    log.info(ccxt_ex.fetch_ticker(symbol))

    cx = CcxtExchange(exchange=ccxt_ex)
    trade_executor = CcxtOrderEngine(cx)

    print()
    print(list(cx.method_list))

    print()
    print(cx.free_balance)

    print(f"fetch my trades {symbol}")
    print(cx.fetch_my_trades(symbol))

    one_day = 24 * 60 * 60 * 1000  # in milliseconds
    since = cx.exchange.milliseconds() - one_day  # last 24 hours in milliseconds
    to = since + one_day
    print(since)

    print(f"fetch closed orders {symbol}")
    print(cx.fetch_closed_orders(symbol, since))

    if cx.method_list['fetchClosedOrders']:
        all_orders = cx.get_all_closed_orders_since_to(symbol, since, to)
        print(all_orders)

    print()
    print(cx.fetch_l2_order_book(symbol))

    print()
    print(cx.fetch_order_book(symbol))