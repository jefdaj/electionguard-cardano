import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture
import logging

LOG = logging.getLogger(__name__)

@per_election_fixture
def oneshot_utxo(ogmios: OgmiosV6ChainContext, funder_keys: KeyPair) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    utxo = pick_oneshot_utxo(ogmios, funder_keys.addr)
    LOG.debug(f'oneshot_utxo: {utxo}')
    return utxo
 
@per_election_fixture
def script(oneshot_utxo: UTxO) -> ElectionScript:
    '''Parameterize the contract with the oneshot_utxo.'''
    script = ElectionScript.from_oneshot_utxo(oneshot_utxo)
    LOG.debug(f'script: {script}')
    return script

@per_election_fixture
def script_addr(script: ElectionScript) -> Address:
    # TODO configure network from cli later?
    addr = Address(script.policy_id, network=Network.TESTNET)
    LOG.debug(f'addr: {addr}')
    return addr
