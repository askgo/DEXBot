import keyring
import keyring.errors


def set_keyring(strategy_name, asset_type, secret):
    try:
        keyring.get_keyring()
        keyring.set_password(strategy_name, asset_type,secret)
    except keyring.errors.PasswordSetError:
        log.info(f"failed to store {asset_type} in Keyring")


def get_keyring(strategy_name, asset_type):
    try:
        keyring.get_keyring()
        secret = keyring.get_password(strategy_name, asset_type)
        return secret
    except keyring.errors.KeyringError:
        log.info(f"failed to retrieve {asset_type} in Keyring")


def del_keyring(strategy_name, asset_type):
    try:
        keyring.get_keyring()
        secret = keyring.delete_password(strategy_name, asset_type)
        return secret
    except keyring.errors.PasswordDeleteError:
        log.info(f"failed to delete {asset_type} in Keyring")


# test
"""
strategy = 'dexbot-arb-cointiger'
asset_type = "apikey"
set_keyring(strategy, asset_type, "#$PUPIO$OIJDSFDF")
secret = get_keyring(strategy, asset_type)
print(f'strategy name: {strategy} asset_type: {asset_type}, secret: {secret}')
del_keyring(strategy, asset_type)
"""

