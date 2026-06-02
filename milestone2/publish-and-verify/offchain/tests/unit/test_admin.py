import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_admin_assets(admin_assets: MultiAsset):
    assert isinstance(admin_assets, MultiAsset)
    # TODO also test it has the STT
