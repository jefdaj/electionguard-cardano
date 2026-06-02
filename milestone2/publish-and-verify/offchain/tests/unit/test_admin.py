import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_admin_assets(admin_assets: MultiAsset):
    LOG.debug(f'admin_assets: {admin_assets}')
    assert isinstance(admin_assets, MultiAsset)
    assert len(admin_assets) == 1
    for script in admin_assets:
        assert len(admin_assets[script]) == 1
        assert AssetName(b'egc-election-admin-stt') in admin_assets[script]
