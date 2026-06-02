import pytest
from pycardano import *
from egc import *

@pytest.fixture(scope='package')
def admin_assets(script: ElectionScript) -> MultiAsset:
    return mint_channel_stt_assets(script.policy_id, 1, [ADMIN_ID])

# TODO later, Admin itself
