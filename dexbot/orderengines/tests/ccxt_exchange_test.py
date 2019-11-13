import sys
sys.path.append("..")

import logging
from ccxt_ex import CcxtExchange
from ccxt_helper import get_ccxt_module, get_cointiger_module, get_exchange_keys, get_exchange_config
import pandas as pd

from cointiger_sdk import cointiger
from cointiger_sdk import const
from datetime import timedelta, timezone, datetime
import time
import json

"""
    Todo: This version to be completed and swapped out with the dexbot version

    Temporary informal unit test for ccxt exchange

    Note: 
    Ccxt Exchange time is 13 digit unix time based on milliseconds for timestamp. 
    Divide by 1000 to convert to 10 digit timestamp in python

    Need to Hard code fees fro Cointiger, not avail through API call. 
    Cointiger is 0.15% for taker and 0.08% for maker

"""
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


def test_print_orderbooks(symbol, cx):
    """
    just print order book data
    :param symbol: ticker symbol
    :param cx: CcxtExchange object
    :return: none
    """
    log.info(f"Fetch Ticker for {symbol} : {cx.fetch_ticker(symbol)}\n")
    log.info(f"Fetching L2 Order Book: {cx.fetch_l2_order_book(symbol)}\n")
    log.info(f"Fetching Order Book: {cx.fetch_order_book(symbol)}\n")


def get_cex_data(l2, depth: int):
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out
    # todo move this method to ccxt_helper
    bids = l2['bids']
    bid_df = pd.DataFrame(bids)
    bid_df.columns = ['price', 'vol']
    # bring down to second level precision not millisecond
    bid_df['timestamp'] = int(l2['timestamp'] / 1000)
    bid_df['type'] = 'bids'

    ask = l2['asks']
    ask_df = pd.DataFrame(ask)
    ask_df.columns = ['price', 'vol']
    # bring down to second level precision not millisecond
    ask_df['timestamp'] = int(l2['timestamp'] / 1000)
    ask_df['type'] = 'asks'

    return ask_df.head(depth), bid_df.head(depth)


def display_orderbook(depth: int, symbol: str, cx: CcxtExchange):
    log.info(f'symbol: {symbol}')
    #   test_print_orderbooks(symbol, cx)

    # fetch current order book with order depth
    l2_ob = cx.fetch_l2_order_book(symbol)
    asks, bids = get_cex_data(l2_ob, depth)
    pd.options.display.float_format = "{:.8f}".format
    log.info(f'Asks:\n {asks}')
    log.info(f'Bids:\n {bids}')
    return asks, bids


################ fees and trade calc ################################
# to do move these methods to simple arb strategy

def get_fees(cx):
    """ (TODO : incomplete)
    get trading fees from CEX (if available)
    if not available, get static fees (currently None) or user designated fees (todo)
    :param cx: CcxtExchange object
    :return: fees
    """
    # may not exist for some exchanges, check method_list
    method_list = list(cx.method_list)
    # log.info(f"Available Methods from ccxt for this exchange: {list(method_list)}")
    fees = None
    if 'fetchTradingFees' in method_list:
        fees = cx.fetch_trading_fees()
        log.info(f'Fetch Trading Fees: {fees}')
    if fees is None:
        log.info(f'Fees from exchange API is none, switching to manual fee')
    return fees


def calc_trade_amt(percent, price_df, asset, free_bal, min_bal):
    """
    Calculate amount to use for trading based off of existing balance,
    minimum balance to retain, price of asset
    This calculation will take the highest bid and sell your asset at market
    with the intention to clear immediately
    :param percent: percentage of free balance to use
    :param price_df: available market prices from order book
    :param asset: name of asset, e.g. BTS
    :param free_bal: amont of asset available in on-exchange account
    :param min_bal: minimum percentage of balance to retain for purposes of fees.
    :return: buy or sell amount and price, or 0,0 for no trade action
    """
    if asset in free_bal:
        amt_free = free_bal[asset]
        log.info(f"Inside Calc_trade_amt: {asset} : Free: {amt_free}")
        if amt_free > 0:
            amt_avail = amt_free - (amt_free * min_bal)
            buy_amt = amt_avail * percent
            buy_price = price_df['price'][0]  # take the lowest asking price for market buy
            return buy_amt, buy_price
        else:
            return 0, 0
    else:
        return 0, 0


def get_timedelta(time_frame):
    """
    get since_ts based on time frame in minues
    :param time_frame: time in minutes
    :return: time delta (based on utc)
    """
    # Time management
    now_ts = datetime.now(timezone.utc)
    dt = now_ts - timedelta(minutes=time_frame)
    since_ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
    log.info(f'Now Timestamp {int(now_ts.replace(tzinfo=timezone.utc).timestamp())},'
             f'Time 10 minutes ago: {since_ts}')
    return since_ts


def setup_cointiger(config_file):
    """
    configure cointiger exchange with config file
    set api_key and secret value in cointiger exchage
    :param config_file: config file name
    :return: api_key from file
    """
    api_key = get_cointiger_module(config_file)
    return api_key


def ct_cancel_order(api_key, order_id, symbol):
    cancel_data = {
        'api_key': api_key,
        'orderIdList': '{' + symbol + ':[' + str(order_id) + ']}',
        'time': int(time.time()),
    }
    log.info(cancel_data)

    try:
        log.info("COINTIGER BATCH CANCEL")
        cancel_response = cointiger.batch_cancel(dict(cancel_data, **{'sign': cointiger.get_sign(cancel_data)}))
        log.info(cancel_response)

        order_id = None
        cancel_dict = json.loads(cancel_response)
        code_resp = cancel_dict['code']
        if code_resp == '0':
            log.info(f"SUCCESS: {cancel_dict}")
            order_id = cancel_dict['data']['success'][0]

        return order_id, code_resp
    except Exception as e:
        log.error(e)


def ct_place_order(api_key, price, volume, symbol, side_type):
    """
    Place order on cointiger exchange
    :param api_key: api key
    :param price: price to sell
    :param volume: volume of asset to sell
    :param symbol: symbol
    :param side_type: 'buy' or 'sell' for transaction
    :return: order_id, code_response if success or not (0 is succcess, 1 or 2 is error)
    """
    side = const.SideType.SELL.value
    if side_type is 'buy':
        side = const.SideType.BUY.value

    order_data = {
        'api_key': api_key,
        'symbol': symbol,
        'price': str(price),
        'volume': str(volume),
        'side': side,
        'type': const.OrderType.LimitOrder.value,
        'time': int(time.time())
    }
    try:
        log.info(f'order data: {order_data}')
        log.info("COINTIGER: get signature from order data")
        log.info(cointiger.get_sign(order_data))
        log.info("COINTIGER PLACE ORDER")
        ct_response = cointiger.order(dict(order_data, **{'sign': cointiger.get_sign(order_data)}))
        log.info(ct_response)

        order_id = None
        ct_dict = json.loads(ct_response)
        code_resp = ct_dict['code']
        log.info(f'Code response from COINTIGER {code_resp}')

        if code_resp == '0':
            order_id = ct_dict['data']['order_id']  # get zeroth order id
            log.info(f"Order ID FROM COINTIGER ORDER: {order_id}")
        return order_id, code_resp
    except Exception as e:
        log.error(e)


if __name__ == '__main__':

    symbol = 'BTS/ETH'
    bitshares_symbol = 'BTS/OPEN.ETH'
    ct_symbol = symbol.replace('/', '').lower()

    ask_symbol = symbol.split('/')[0]
    bid_symbol = symbol.split('/')[1]
    log.info(f'CEX Price: Ask Symbol ({ask_symbol}), Vol is Amount: Bid Symbol: ({bid_symbol})')

    exch_name = 'cointiger'
    # update this to reflect your config file
    config_file = "ccxt_config/secrets_test.ini"
    api_key = setup_cointiger(config_file) # redundant, use cointiger_ex.
    # todo: need to test using cointiger_ex. py and ccxt_ex.py refactored

    config_sections = get_exchange_config(config_file, exch_name)
    apikey, secret = get_exchange_keys(config_sections, exch_name)
    cx = CcxtExchange(exch_name, symbol, api_key, secret)

    depth = 2
    asks, bids = display_orderbook(depth, symbol, cx)

    """
    test buy and sell on cex exchanges
    """
    free_bal = cx.free_balance
    log.info(f"All Available Free Balance: {free_bal}")
    log.info("################################")

    # test sell 5% of free balance

    percent = 0.6
    min_bal_percentage = 0.10  # do not use 10% of free balance, keep at least 10% around.
    sell_amt, sell_price = calc_trade_amt(percent, bids, ask_symbol, free_bal, min_bal_percentage)
    log.info(f"Preparing Market Sell Order: {ask_symbol}, Amt: {sell_amt}, Price:{sell_price}")

    sell_price = 0.00016
    sell_amt = 320
    side_type = 'sell'

    # todo: integrate ct_place_order and ct_cancel_order methods into cointiger_exchange class,
    # which inherits CcxtExchange and overrides buy and sell orders as cancel orders

    order_id, code_resp = ct_place_order(api_key, sell_price, sell_amt, ct_symbol, side_type)
    log.info(f"printing Order_ID: {order_id}")
    cancel_id = ct_cancel_order(api_key, order_id, ct_symbol)

    # todo
    time_frame = 2880  # 2 days ago - 60m*48
    # how far back should we look in time. 10 minutes
    since_ts = get_timedelta(time_frame)

    log.info("################################")
    # keep checking status of order
    while True:
        if 'fetchMyTrades' in cx.method_list:
            log.info(f'fetch my trades: {cx.fetch_my_trades(symbol)}')
        if 'fetchOpenOrders' in cx.method_list:
            log.info(f'fetch open orders: {cx.fetch_open_orders(symbol)}')
        if 'fetchClosedOrders' in cx.method_list:
            log.info(f'fetch closed orders: {cx.fetch_closed_orders(symbol, since_ts * 1000)}')

    # todo:
    #   cx.cancel_order(order_id, symbol, {}):
    #   all_orders = cx.get_all_closed_orders_since_to(symbol, since, to)
    #   log.info(f"Fetching All closed Orders for {symbol} since {since} to {to} : {all_orders}")