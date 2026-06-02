import pytest
from egc import *


### dev wallet things are session scoped ###

# @pytest.fixture(scope='session')
# def funder_sk() -> SigningKey:
#     return load_wallet_signing_key(name='dev')

# @pytest.fixture(scope='session')
# def funder_addr() -> Address:
#     return load_wallet_addr(name='dev')

# @pytest.fixture(scope='session')
# def funder_vkh(funder_sk: SigningKey) -> VerificationKeyHash:
#     return vkh_for_signing_key(funder_sk)

@pytest.fixture(scope='session')
def funder_keys() -> KeyPair:
    kp = KeyPair(name='dev', verbose=False) # leave default, global keys_dir
    return kp

### the rest is package scoped (per election) ###

@pytest.fixture(scope='package')
def oneshot_utxo(ogmios: OgmiosV6ChainContext, funder_keys: KeyPair) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    return pick_oneshot_utxo(ogmios, funder_keys.addr)
 
# @pytest.fixture(scope='package')
# def script(oneshot_utxo: UTxO) -> ElectionScript:
#     '''Parameterize the contract with the oneshot_utxo.'''
#     return ElectionScript(oneshot_utxo)

# @pytest.fixture(scope='package')
# def funder(
#         funder_sk: SigningKey,
#         funder_addr: Address,
#         funder_vkh: VerificationKeyHash,
#     ) -> Funder:
#     pass
