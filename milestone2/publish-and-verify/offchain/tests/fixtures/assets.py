import pytest
from pycardano import *
from egc import *
from typing import List
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='package')
def admin_id() -> ChannelId:
    LOG.info(f'admin_id: {ADMIN_CHANNEL_ID}')
    return ADMIN_CHANNEL_ID

@pytest.fixture(scope='package')
def admin_assets(script: ElectionScript) -> MultiAsset:
    return mint_channel_stt_assets(script.policy_id, 1, [ADMIN_CHANNEL_ID])

@pytest.fixture(scope='package')
def subchannel_ids() -> List[ChannelId]:
    strs = ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']
    ids = [ChannelIdHelper.from_string(s) for s in strs]
    LOG.info(f'subchannel_ids: {ids}')
    return ids

@pytest.fixture(scope='package')
def subchannel_assets(
        script: ElectionScript,
        subchannel_ids: List[ChannelId]
    ) -> MultiAsset:
    assets = mint_channel_stt_assets(script.policy_id, 1, subchannel_ids)
    LOG.info(f'subchannel_stt_assets: {assets}')
    return assets
