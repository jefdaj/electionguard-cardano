import pytest
from pycardano import *
from egc import *

@pytest.fixture(scope='session')
def funder_keys() -> KeyPair:
    kp = KeyPair(name='dev', verbose=False) # leave default, global keys_dir
    return kp

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

@pytest.fixture(scope='package')
def funder(funder_keys: KeyPair) -> Funder:
    return Funder(key_pair=funder_keys)

@pytest.fixture(scope='package')
def init_tx(
        funder: Funder,
        script: ElectionScript,
        admin_vkh: VerificationKeyHash,
    ) -> TransactionBuilder:
    return funder.build_init_tx(
        script=script,
        admin_vkh=admin_vkh,
        admin_ada=100
    )
