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
            ('binance', 'Binance')
        ]

        simplearb_orders_config = [
            ConfigElement('cex_price_source', 'choice', EXCHANGES[0][0], 'Select a CEX',
                          'The bot will arb with this Centralized Exchange', EXCHANGES),
            ConfigElement('cex_apikey', 'string', '', 'API Key', 'Enter CEX API key here', ''),
            ConfigElement('cex_secret', 'string', '', 'Secret', 'Enter CEX Secret here', ''),
            ConfigElement('cex_market', 'string', 'BTS/ETH', 'Market',
                          'CEX market to operate on, in the format QUOTE/BASE',
                          r'[A-Z0-9\.]+[:\/][A-Z0-9\.]+'),
            ConfigElement('market_depth_amount', 'int', 2, 'Market depth',
                          'From what order depth will market trade opportunities measured? ',
                          (1, 100, 2, '')),
            ConfigElement('spread', 'float', 5, 'Spread',
                          'The min percentage spread in order to arb', (0, 100, 2, '%')),
            ConfigElement('reserve_amt', 'float', 5, 'Percentage to reserve',
                          'Percentage to reserve for fees', (0, 100, 2, '%')),
            ConfigElement('expiration_time', 'int', 3, 'Order expiration time in seconds',
                          'Define order expiration time in seconds for reset, suggest 3',
                          (1, 10, ''))
        ]

        return BaseConfig.configure(return_base_config) + simplearb_orders_config

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
