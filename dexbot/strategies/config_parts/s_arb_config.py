from dexbot.strategies.config_parts.base_config import BaseConfig, ConfigElement


class SimpleArbConfig(BaseConfig):

    @classmethod
    def configure(cls, return_base_config=True):
        """ Return a list of ConfigElement objects defining the configuration values for this class.

            User interfaces should then generate widgets based on these values, gather data and save back to
            the config dictionary for the worker.

            NOTE: When overriding you almost certainly will want to call the ancestor and then
            add your config values to the list.

            :param return_base_config: bool:
            :return: Returns a list of config elements
        """
        # External exchanges for simple arb strategy
        EXCHANGES = [
            ('cointiger', 'CoinTiger'),
            ('bitfinex', 'Bitfinex'),
            ('binance', 'Binance')
        ]

        simplearb_config = [
            ConfigElement('cex_exchange,'
                          'choice',
                          EXCHANGES[0][0],
                          'CEX Exchange Source',
                          'The bot will try to get price information from this source',
                          EXCHANGES),
            ConfigElement('relative_order_size',
                          'bool',
                          False,
                          'Relative order size',
                          'Amount is expressed as a percentage of the account balance of quote/base asset',
                          None),
            ConfigElement('amount',
                          'float',
                          1,
                          'Amount',
                          'Fixed order size, expressed in quote asset, unless "relative order size" selected',
                          (0, None, 8, '')),
            ConfigElement('spread',
                          'float',
                          5,
                          'Spread',
                          'The percentage difference between buy and sell',
                          (0, 100, 2, '%')),
            ConfigElement('market_depth_amount',
                          'float',
                          0,
                          'Market depth',
                          'From which depth will market spread be measured? (QUOTE amount)',
                          (0.00000001, 1000000000, 8, '')),
            ConfigElement('price_change_threshold',
                          'float',
                          2,
                          'Price change threshold',
                          'Define center price threshold to react on',
                          (0, 100, 2, '%')),
            ConfigElement('expiration_time',
                          'int',
                          157680000,
                          'Order expiration time',
                          'Define custom order expiration time to force orders reset more often, seconds',
                          (30, 157680000, ''))
        ]

        return BaseConfig.configure(return_base_config) + simplearb_config

    @classmethod
    def configure_details(cls, include_default_tabs=True):
        """ Return a list of ConfigElement objects defining the configuration values for this class.

            User interfaces should then generate widgets based on these values, gather data and save back to
            the config dictionary for the worker.

            NOTE: When overriding you almost certainly will want to call the ancestor and then
            add your config values to the list.

            :param include_default_tabs: bool:
            :return: Returns a list of Detail elements
        """
        return BaseConfig.configure_details(include_default_tabs) + []
