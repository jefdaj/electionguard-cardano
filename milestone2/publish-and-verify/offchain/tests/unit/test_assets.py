import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.mark.testnet
def test_admin_assets(script: ElectionScript, admin_assets: MultiAsset):
    assert isinstance(admin_assets, MultiAsset)
    assert len(admin_assets) == 1
    assert script.policy_id in admin_assets.keys()
    for policy_id in admin_assets:
        assert len(admin_assets[policy_id]) == 1
        assert AssetName(b'egc-election-admin-stt') in admin_assets[policy_id]

@pytest.mark.testnet
def test_subchannel_assets(script: ElectionScript, subchannel_assets: MultiAsset):
    assert isinstance(subchannel_assets, MultiAsset)
    assert len(subchannel_assets) == 1
    assert script.policy_id in subchannel_assets.keys()
    for policy_id in subchannel_assets:
        assert len(subchannel_assets[policy_id]) == 5
