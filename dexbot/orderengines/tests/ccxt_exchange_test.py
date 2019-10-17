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


def get_exchange_config():
    try:
        config_dir = os.path.dirname(__file__)
        parser = configparser.ConfigParser()
        parser.read(os.path.join(config_dir, config_file))
        exch_ids = parser.sections()

        sec = {section_name: dict(parser.items(section_name)) for section_name in exch_ids}
        return sec
    except Exception as e:
        log.error(e)
        pass

def get_exchange(config_sections):
    # need to fix below in order to check for for acceptable exchanges and parameters
    # for now, get 0th exchange
    exch_name = list(config_sections)[0]
    apikey = config_sections[exch_name]['api_key']
    secret = config_sections[exch_name]['secret']
    log.info(f"API Key:  {apikey}")
    log.info(f"SECRET: {secret})")

    # coin tiger requires an API key, even if only for ticker data
    ccxt_ex = getattr(ccxt, exch_name)({
        "apiKey": apikey,
        "secret": secret,
        'timeout': 30000,
        'enableRateLimit': True,
        'verbose': False,
    })
    #log.info(f"Fetch Ticker for {symbol} : {ccxt_ex.fetch_ticker(symbol)}\n")
    return ccxt_ex


if __name__ == '__main__':

    log = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    symbol = 'BTC/USDT'
    log.info("symbol: {} ".format(symbol))

    config_sections = get_exchange_config()
    log.info(config_sections)
    ccxt_ex = get_exchange(config_sections)

    cx = CcxtExchange(exchange=ccxt_ex)
    trade_executor = CcxtOrderEngine(cx)
    log.info(f"Available Free Balance: {cx.free_balance}\n")

    """
    log.info(f"Available Methods from ccxt for this exchange {list(cx.method_list)}\n")
    log.info(f"Fetch my trades {symbol}: Trades: {cx.fetch_my_trades(symbol)}\n")

    one_day = 24 * 60 * 60 * 1000  # in milliseconds
    since = cx.exchange.milliseconds() - one_day  # last 24 hours in milliseconds
    to = since + one_day
    log.info(since)
    
    log.info(f"fetch closed orders for {symbol}: {cx.fetch_closed_orders(symbol, since)}\n")
    
    if cx.method_list['fetchClosedOrders']:
        all_orders = cx.get_all_closed_orders_since_to(symbol, since, to)
        log.info(f"Fetching All closed Orders for {symbol} since {since} to {to} \n")
        log.info(all_orders)

    l2 = cx.fetch_l2_order_book(symbol)
    log.info(f"Fetching L2 Order Book: {cx.fetch_l2_order_book(symbol)}\n")

    log.info(f"Fetching Order Book: {cx.fetch_order_book(symbol)}\n")
    """



