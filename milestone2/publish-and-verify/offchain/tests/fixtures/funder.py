import pytest
from egc import *


### dev wallet things are session scoped ###

@pytest.fixture(scope='session')
def funder_sk() -> SigningKey:
    return load_wallet_signing_key(name='dev')

@pytest.fixture(scope='session')
def funder_addr() -> Address:
    return load_wallet_addr(name='dev')

@pytest.fixture(scope='session')
def funder_vkh(funder_sk: SigningKey) -> VerificationKeyHash:
    return vkh_for_signing_key(funder_sk)


### the rest is package scoped (per election) ###

@pytest.fixture(scope='package')
def oneshot_utxo(ogmios: OgmiosV6ChainContext, funder_addr: Address) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    return pick_oneshot_utxo(ogmios, funder_addr)
 
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
