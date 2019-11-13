import abc

class CentralizedExchange(metaclass=abc.ABCMeta):
    """
    This class is an Abstract base class for consistent method names for various CEX.
    A strategy using the CEX can have more than one exchange connection.
    Some are covered by ccxt, but others require a separate implementation.
    Cointiger is not ccxt certified and the v2 of their API has yet to be integrated into CCXT

    """
    def __init__(self, exch_name, symbol, api_key, secret):
        self.api_key = api_key
        self.secret = secret
        self.symbol = symbol
        self.exch_name = exch_name

    @property
    @abc.abstractmethod
    def method_list(self):
        pass

    @property
    @abc.abstractmethod
    def free_balance(self):
        pass

    @abc.abstractmethod
    def fetch_trading_fees(self):
        pass

    @abc.abstractmethod
    def fetch_open_orders(self, symbol: str = None):
        pass

    @abc.abstractmethod
    def fetch_order(self, order_id: int):
        pass

    @abc.abstractmethod
    def cancel_order(self, order_id: int, symbol: str):
        pass

    @abc.abstractmethod
    def create_sell_order(self, symbol: str, amount: float, price: float):
        pass

    @abc.abstractmethod
    def create_buy_order(self, symbol: str, amount: float, price: float):
        pass

    @abc.abstractmethod
    def fetch_closed_orders(self, symbol: str, since: str):
        pass

    @abc.abstractmethod
    def fetch_my_trades(self, symbol: str):
        pass

    @abc.abstractmethod
    def get_all_closed_orders_since_to(self, symbol, since, to):
        pass

    @abc.abstractmethod
    def fetch_l2_order_book(self, symbol: str):
        pass

    @abc.abstractmethod
    def fetch_order_book(self, symbol: str):
        pass

