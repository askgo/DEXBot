from dexbot.orderengines.cex import CentralizedExchange

from cointiger_sdk import cointiger
from cointiger_sdk import const
import logging


class CoinTiger(CentralizedExchange):
    """
    https://github.com/cointiger/api-docs-en/wiki/REST-Api-List
    """

    def __init__(self, exchange):
        self.exchange = exchange
        log = logging.getLogger(__name__)
        log.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s'
        )


