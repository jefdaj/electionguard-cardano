import pytest
from pycardano import *
from egc import *
from tests.helpers import per_election_fixture
import logging

# TODO are the conftests not importing anything? why is this needed?
from .network import *

LOG = logging.getLogger(__name__)

@per_election_fixture
def oneshot_utxo(ogmios: OgmiosV6ChainContext, funder_address: Address) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    utxo = pick_oneshot_utxo(ogmios, funder_address)
    LOG.debug(f'oneshot_utxo: {utxo}')
    print(f'oneshot_utxo: {utxo}')
    return utxo
 
@per_election_fixture
def script(oneshot_utxo: UTxO) -> ElectionScript:
    '''Parameterize the contract with the oneshot_utxo.'''
    oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
    script = ElectionScript.from_oneshot_hex(oneshot_hex)
    LOG.debug(f'script: {script}')
    return script

@per_election_fixture
def script_addr(script: ElectionScript) -> Address:
    addr = Address(script.policy_id, network=Network.TESTNET) # TODO dynamic network
    LOG.debug(f'addr: {addr}')
    return addr
