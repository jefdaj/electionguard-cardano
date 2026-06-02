import pytest

pytest_plugins = [
    "fixtures.ogmios",
    "fixtures.funder",
    "fixtures.election",
]

# import json
# from os.path import realpath, join, exists
# from pathlib import Path
# from pycardano import OgmiosV6ChainContext, Address, SigningKey, VerificationKeyHash, UTxO, MultiAsset
# from typing import Dict, List

# from election import wallet as ew
# from election import plutus as ep
# from election.plutus import script as eps
# from election.plutus.types.channel_id import *
# from election.roles import funder as erf

# TODO helper fn rather than fixture?
# @pytest.fixture(scope='package')
# def admin_id() -> ChannelId:
#     LOG.info('admin_id fixture')
#     return ChannelIdHelper.from_string('admin')

# TODO helper fn rather than fixture?
# @pytest.fixture(scope='package')
# def subchannel_ids() -> List[ChannelId]:
#     LOG.info('subchannel_ids fixture')
#     strs = ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']
#     return [ChannelIdHelper.from_string(s) for s in strs]

# TODO helper fn rather than fixture?
# @pytest.fixture(scope='package')
# def subchannel_stt_assets(
#         script: eps.ElectionScript,
#         subchannel_ids: List[ChannelId]
#     ) -> MultiAsset:
#     LOG.info('subchannel_stt_assets fixture')
#     return erf.mint_channel_stt_assets(script.policy_id, 1, subchannel_ids)
