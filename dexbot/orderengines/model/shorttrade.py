from model.trade import Trade


class ShortTrade(Trade):
    def __init__(self,
                 start_price: float,
                 symbol: str,
                 amount: float,
                 percent_change: float = 0.5,
                 stop_percent_change: float = 0.5,
                 currency: str = "USD") -> None:
        super().__init__(start_price, symbol, amount, currency)

        self.target_price = start_price * (1 - percent_change / 100)
        self.stop_price = start_price * (1 + stop_percent_change / 100)

    @property
    def exit_price(self):i
        return self.target_price

    @property
    def stop_loss(self):
        return self.stop_price

    def __str__(self) -> str:
        return "Short " + super().__str__()
