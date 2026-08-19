import pytest
from pycardano import *
from egc import *
from typing import List
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='module')
def admin_id() -> ChannelId:
    LOG.debug(f'admin_id: {ADMIN_CHANNEL_ID}')
    return ADMIN_CHANNEL_ID

@pytest.fixture(scope='module')
def admin_assets(script: ElectionScript) -> MultiAsset:
    return mint_channel_stt_assets(script.policy_id, 1, [ADMIN_CHANNEL_ID])

@pytest.fixture(scope='module')
def subchannel_ids() -> List[ChannelId]:
    strs = ['device1', 'guardian1', 'guardian2', 'guardian3', 'verifier1']
    ids = sorted([coerce_channel_id(s) for s in strs]) # should match aiken sort
    LOG.debug(f'subchannel_ids: {ids}')
    return ids

@pytest.fixture(scope='module')
def subchannel_assets(
        script: ElectionScript,
        subchannel_ids: List[ChannelId]
    ) -> MultiAsset:
    assets = mint_channel_stt_assets(script.policy_id, 1, subchannel_ids)
    LOG.debug(f'subchannel_stt_assets: {assets}')
    return assets
