from dexbot.orderengines.ccxt_ex import CcxtExchange
from cointiger_sdk import cointiger
from cointiger_sdk import const
import logging
import time
import json

class CoinTiger(CcxtExchange):
    """
    https://github.com/cointiger/api-docs-en/wiki/REST-Api-List
    """

    def __init__(self, exch_name, symbol, api_key, secret):
        super().__init__(exch_name, symbol, api_key, secret)
        self.cointiger = cointiger.set_key_and_secret(self.api_key, self.secret)
        self.ct_symbol = self.symbol.replace('/', '').lower()


        self.log = logging.LoggerAdapter(
                logging.getLogger('dexbot.orderengines.ccxt_exchange'), {})


    def fetch_trading_fees(self):
            """
            get trading fees
            :return:
            """
            # Cointiger is 0.15% for taker and 0.08% for maker
            fees = { 'maker': 0.0015, 'taker': 0.0008 }
            return fees


    def cancel_order(self, order_id: int, symbol: str):
        cancel_data = {
            'api_key': self.api_key,
            'orderIdList': '{' + symbol + ':[' + str(order_id) + ']}',
            'time': int(time.time()),
        }
        self.log.info(cancel_data)

        try:
            self.log.info("COINTIGER BATCH CANCEL")
            cancel_response = cointiger.batch_cancel(dict(cancel_data, **{'sign': cointiger.get_sign(cancel_data)}))
            self.log.info(cancel_response)

            order_id = None
            cancel_dict = json.loads(cancel_response)
            code_resp = cancel_dict['code']
            if code_resp == '0':
                self.log.info(f"SUCCESS: {cancel_dict}")
                order_id = cancel_dict['data']['success'][0]

            return order_id, code_resp
        except Exception as e:
            self.log.error(e)


    def ct_place_order(self, symbol, price, volume, side_type):
        """
        Place order on cointiger exchange
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
            'api_key': self.api_key,
            'symbol': symbol,
            'price': str(price),
            'volume': str(volume),
            'side': side,
            'type': const.OrderType.LimitOrder.value,
            'time': int(time.time())
        }
        try:
            self.log.info(f'order data: {order_data}')
            self.log.info("COINTIGER: get signature from order data")
            self.log.info(cointiger.get_sign(order_data))
            self.log.info("COINTIGER PLACE ORDER")
            ct_response = cointiger.order(dict(order_data, **{'sign': cointiger.get_sign(order_data)}))
            self.log.info(ct_response)

            order_id = None
            ct_dict = json.loads(ct_response)
            code_resp = ct_dict['code']
            self.log.info(f'Code response from COINTIGER {code_resp}')

            if code_resp == '0':
                order_id = ct_dict['data']['order_id'] # get zeroth order id
                self.log.info(f"Order ID FROM COINTIGER ORDER: {order_id}")
            return order_id, code_resp
        except Exception as e:
            self.log.error(e)


    def create_sell_order(self, symbol: str, amount: float, price: float):
        symbol = symbol.replace('/', '').lower() # cointiger symbol has no slash and is lower
        self.ct_place_order(symbol, price, amount, 'sell')

    def create_buy_order(self, symbol: str, amount: float, price: float):
        symbol = symbol.replace('/', '').lower() # cointiger symbol has no slash and is lower
        self.ct_place_order(symbol, price, amount, 'buy')
