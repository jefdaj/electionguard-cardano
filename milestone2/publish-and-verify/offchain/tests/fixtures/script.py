import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='package')
def oneshot_utxo(ogmios: OgmiosV6ChainContext, funder_keys: KeyPair) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    utxo = pick_oneshot_utxo(ogmios, funder_keys.addr)
    LOG.debug(f'oneshot_utxo: {utxo}')
    return utxo
 
@pytest.fixture(scope='package')
def script(oneshot_utxo: UTxO) -> ElectionScript:
    '''Parameterize the contract with the oneshot_utxo.'''
    script = ElectionScript.from_oneshot_utxo(oneshot_utxo)
    LOG.debug(f'script: {script}')
    return script

@pytest.fixture(scope='package')
def script_addr(script: ElectionScript) -> Address:
    # TODO configure network from cli later?
    addr = Address(script.policy_id, network=Network.TESTNET)
    LOG.debug(f'addr: {addr}')
    return addr
