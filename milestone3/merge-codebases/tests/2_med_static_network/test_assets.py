import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_admin_stt(script: ElectionScript, admin_assets: MultiAsset):
    assert isinstance(admin_assets, MultiAsset)
    assert len(admin_assets) == 1
    assert script.policy_id in admin_assets.keys()
    for policy_id in admin_assets:
        assert len(admin_assets[policy_id]) == 1
        assert AssetName(b'election-admin') in admin_assets[policy_id]

def test_subchannel_stts(script: ElectionScript, subchannel_assets: MultiAsset):
    assert isinstance(subchannel_assets, MultiAsset)
    assert len(subchannel_assets) == 1
    assert script.policy_id in subchannel_assets.keys()
    for policy_id in subchannel_assets:
        assert len(subchannel_assets[policy_id]) == 5
