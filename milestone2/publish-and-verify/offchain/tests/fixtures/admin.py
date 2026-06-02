import pytest
from pycardano import *
from egc import *

@pytest.fixture(scope='package')
def admin_keys(keys_dir: Path) -> KeyPair:
    kp = KeyPair(keys_dir=keys_dir, name='admin', verbose=False)
    return kp

@pytest.fixture(scope='package')
def admin_vkh(admin_keys: KeyPair) -> VerificationKeyHash:
    return admin_keys.vkh

@pytest.fixture(scope='package')
def admin_assets(script: ElectionScript) -> MultiAsset:
    return mint_channel_stt_assets(script.policy_id, 1, [ADMIN_CHANNEL_ID])

# TODO later, Admin itself
