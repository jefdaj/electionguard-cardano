import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture
from typing import List
import logging

LOG = logging.getLogger(__name__)

@per_election_fixture
def admin_id() -> ChannelId:
    LOG.info(f'admin_id: {ADMIN_CHANNEL_ID}')
    return ADMIN_CHANNEL_ID

@per_election_fixture
def admin_assets(script: ElectionScript) -> MultiAsset:
    return mint_channel_stt_assets(script.policy_id, 1, [ADMIN_CHANNEL_ID])

@per_election_fixture
def subchannel_ids() -> List[ChannelId]:
    strs = ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']
    ids = [ChannelIdHelper.from_string(s) for s in strs]
    LOG.info(f'subchannel_ids: {ids}')
    return ids

@per_election_fixture
def subchannel_assets(
        script: ElectionScript,
        subchannel_ids: List[ChannelId]
    ) -> MultiAsset:
    assets = mint_channel_stt_assets(script.policy_id, 1, subchannel_ids)
    LOG.info(f'subchannel_stt_assets: {assets}')
    return assets
