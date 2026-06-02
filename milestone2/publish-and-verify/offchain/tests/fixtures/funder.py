import pytest
from egc import *

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
