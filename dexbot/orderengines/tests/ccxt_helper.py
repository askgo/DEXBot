import logging
import os
import configparser
import ccxt
import pandas as pd
from cointiger_sdk import cointiger


"""
The purpose of this class is to help setup ccxt exchange configuration. 
Also to read and write orderbooks (in dataframe format) to file.
"""

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


def get_exchange_config(config_filename, exch_name):
    """
    use this method for testing, not in dexbot production
    get exchange config based on filename

    :param config_filename:  name of config file
    :param exch_name:  exchange name
    :return:  dict that contains config file section
    """
    try:
        config_dir = os.path.dirname(__file__)
        parser = configparser.ConfigParser()
        parser.read(os.path.join(config_dir, config_filename))
        exch_ids = parser.sections()
        log.info(f'config file: {config_dir}, {config_filename}')
        log.info(f"exchange ids {exch_ids}")
        if exch_name in exch_ids:
            sec = { exch_name: dict(parser.items(exch_name)) }
#            sec = {section_name: dict(parser.items(section_name)) for section_name in exch_ids}
        return sec
    except (FileNotFoundError, PermissionError, OSError) as e:
        log.error(e)
        pass

def get_exchange_keys(config_sections, exch_name):
    """
    Get exchange keys from config_sections
    :param config_sections: config section from parser
    :param exch_name: name of exchange
    :return: apikey and secret
    """
    if exch_name is not list(config_sections)[0]:
        return None, None, None

    apikey = config_sections[exch_name]['api_key']
    secret = config_sections[exch_name]['secret']
    strategy = config_sections[exch_name]['strategy']

    log.info(f"API Key:  {apikey}")
    log.info(f"SECRET: {secret})")
    log.info(f"strategy:  {strategy}")

    return apikey, secret

def get_cointiger_module(config_file):
    """
    instantiate a cointiger module from the cointiger sdk
    cointiger sdk at https://github.com/CoinTiger/CoinTiger_SDK_Python
    :param config_file:
    :param exch_name: cointiger
    :return: api_key
    """
    exch_name = 'cointiger'
    config_sections = get_exchange_config(config_file, exch_name)
    log.info(config_sections)
    api_key, secret = get_exchange_keys(config_sections, exch_name)

    setkey = cointiger.set_key_and_secret(api_key, secret)
    log.info(f'setting api key, secret : {setkey}')
    return api_key


def get_ccxt_module(config_file, exch_name):
    """
    instantiate a ccxt module from the config file name and exchange name
    :return: ccxt module
    """
    config_sections = get_exchange_config(config_file, exch_name)
    log.info(config_sections)

    apikey, secret = get_exchange_keys(config_sections, exch_name)

    # coin tiger requires an API key, even if only for ticker data
    # other exchanges do not need the API key unless trading.
    ccxt_ex = getattr(ccxt, exch_name)({
        "apiKey": apikey,
        "secret": secret,
        'timeout': 30000,
        'enableRateLimit': True,
        'verbose': False,
        'precision': {'price': 8,
                      'amount': 8, }
    })
    return ccxt_ex


def get_cex_data(l2, depth: int):
    """
    sort price and volume data by asks and bids
    reshape into a dataframe and return

    :param l2: level 2 orderbook from cex exchange
    :param depth: how many orders deep
    :return: asks dataframe, bids dataframe
    """
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out

    bids = l2['bids']
    bid_df = pd.DataFrame(bids)
    bid_df.columns = ['price', 'vol']
    # bring down to second level precision not millisecond
    bid_df['timestamp'] = int(l2['timestamp']/1000)
    bid_df['type'] = 'bids'

    ask = l2['asks']
    ask_df = pd.DataFrame(ask)
    ask_df.columns = ['price', 'vol']
    # bring down to second level precision not millisecond
    ask_df['timestamp'] = int(l2['timestamp']/1000)
    ask_df['type'] = 'asks'

    return ask_df.head(depth), bid_df.head(depth)




