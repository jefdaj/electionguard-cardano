import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='package')
def oneshot_utxo(ogmios: OgmiosV6ChainContext, funder_keys: KeyPair) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    return pick_oneshot_utxo(ogmios, funder_keys.addr)
 
@pytest.fixture(scope='package')
def script(oneshot_utxo: UTxO) -> ElectionScript:
    '''Parameterize the contract with the oneshot_utxo.'''
    return ElectionScript.from_oneshot_utxo(oneshot_utxo)

@pytest.fixture(scope='package')
def script_addr(script: ElectionScript) -> Address:
    # TODO configure network from cli later?
    return Address(script.policy_id, network=Network.TESTNET)
