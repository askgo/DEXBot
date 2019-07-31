import ccxt
from ccxt import ExchangeNotAvailable
from ccxt import OrderNotFound
import logging


class CcxtExchange:

    def __init__(self, exchange=None):
        """
        load_markets() method will request markets, that can later be accessed as a property
        see Market Cache Force Reload in api docs for more details on how this works.

        :param exchange:
        """
        self.exchange = exchange
        self.exchange.load_markets()

        self.log = logging.LoggerAdapter(
                logging.getLogger('dexbot.orderengines.ccxt_exchange'), {})

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
        )

    @property
    def method_list(self):
        """
        Not all exchanges have methods available through ccxt.
        this method returns a dataframe with a list of methods 
        for this specific exchange denoted as true

        :return: dict
        """
        methods_avail = self.exchange.has
        return {key: value for key, value in methods_avail.items() if value is True}

    @property
    def free_balance(self):
        """
        List current non zero balance for all assets on exchange.

        :return: dict
        """
        try:
            balance = self.exchange.fetch_free_balance()
            # there are balances with 0, so we need to filter these out
            return {key: value for key, value in balance.items() if value > 0}
        except ccxt.BaseError as e:
            self.log.exception("free_balance exception {}".format(str(e)))
            raise e

    #todo: need to test this method
    def fetch_trading_fees(self):
        """
        get trading fees for a specific symbol
        :return:
        """
        try:
            #old - return self.exchange.fetch_trading_fees(symbol=symbol, {})
            if self.exchange.has['fetchTradingFees']:
                return self.exchange.fetch_trading_fees({})
        except ccxt.BaseError as e:
            self.log.exception("fetch_trading_fees exception {}".format(str(e)))
            raise e

    def fetch_open_orders(self, symbol: str = None):
        """
        get open orders from ccxt exchange for symbol
        :param symbol:
        :return:
        """
        try:
            return self.exchange.fetch_open_orders(symbol=symbol)
        except ccxt.BaseError as e:
            self.log.exception("fetch_open_orders exception {}".format(str(e)))
            raise e

    def fetch_order(self, order_id: int):
        """
        get order based on order id

        :param order_id:
        :return:
        """
        try:
            return self.exchange.fetch_order(order_id)
        except ccxt.BaseError as e:
            self.log.exception("fetch_order exception {}".format(str(e)))
            raise e

    def cancel_order(self, order_id: int):
        """
        cancel order based on order_id

        :param order_id:
        :return:
        """
        try:
            self.exchange.cancel_order(order_id)
        except OrderNotFound:
            self.log.exception("cancel_order exception {}".format(OrderNotFound))
            # treat as success
            pass

    # add method here to cancel all orders

    def create_sell_order(self, symbol: str, amount: float, price: float):
        """
        create sell order based on symbol with amount and price

        :param symbol:
        :param amount:
        :param price:
        :return:
        """
        try:
            return self.exchange.create_order(symbol=symbol, type="limit", side="sell", amount=amount, price=price)
        except ccxt.BaseError as e:
            self.log.exception("create_sell_order exception {}".format(str(e)))
            raise e

    def create_buy_order(self, symbol: str, amount: float, price: float):
        """
        create buy order based on symbol with amount and price

        :param symbol:
        :param amount:
        :param price:
        :return:
        """
        try:
            return self.exchange.create_order(symbol=symbol, type="limit", side="buy", amount=amount, price=price)
        except ccxt.BaseError as e:
            self.log.exception("create_buy_order exception {}".format(str(e)))
            raise e

    def fetch_closed_orders(self, symbol: str, since: str):
        """
        fetch all closed orders for symbol that have occured since time.
        This does not mean filled orders.

        :param symbol:
        :param since:
        :return:
        """
        try:
            return self.exchange.fetch_closed_orders(symbol=symbol, since=since, limit=None, params={})
        except ccxt.BaseError as e:
            self.log.exception("fetch_closed_orders exception {}".format(str(e)))
            raise e

    def fetch_my_trades(self, symbol: str):
        """
        fetch all my trades for symbol

        :param symbol:
        :return:
        """
        try:
            return self.exchange.fetch_my_trades(symbol=symbol)
        except ccxt.BaseError as e:
            self.log.exception("fetch_my_trades exception {}".format(str(e)))
            raise e

    def get_all_closed_orders_since_to(self, symbol, since, to):
        """
        get all closed orders from time `since` up until `to`
        closed orders does not imply they have been filled.

        :param symbol:
        :param since:
        :param to:
        :return:
        """
        result = []
        page = 1
        min_timestamp = to
        print('Fetching all orders since', self.exchange.iso8601(since), since)
        while min_timestamp > since:
            try:
                print('Fetching page', page)
                # params = {'current_page': page}
                # todo: only use params for okex
                orders = self.exchange.fetch_closed_orders(symbol, since, None, {})
                if len(orders):
                    min_timestamp = orders[0]['timestamp']
                    print('Fetched', len(orders), 'orders, the oldest order as of', self.exchange.iso8601(min_timestamp),
                          min_timestamp)
                    result += orders
                    page += 1
                else:
                    min_timestamp = since
            except ExchangeNotAvailable as e:
                self.log.exception("ExchangeNotAvailable {}".format(str(e)))
                pass  # retry
        return result

    #todo: possibly use feeds instead of doing it here?
    def fetch_l2_order_book(self, symbol: str):
        """
        fetch level 2 order book based on symbol

        :param symbol:
        :return:
        """
        try:
            return self.exchange.fetch_l2_order_book(symbol=symbol, limit=None)
        except ccxt.BaseError as e:
            self.log.exception("fetch_l2_order_book exception {}".format(str(e)))
            raise e

    def fetch_order_book(self, symbol: str):
        """
        fetch order book based on symbol

        :param symbol:
        :return:
        """
        try:
            return self.exchange.fetch_order_book(symbol=symbol, limit=None)
        except ccxt.BaseError as e:
            self.log.exception("fetch_order_book exception {}".format(str(e)))
            raise e
