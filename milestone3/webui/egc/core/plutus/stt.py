from .types.channel_id import *
import logging
from pprint import pformat

LOG = logging.getLogger(__name__)

from pycardano import *

# This should match the one defined in aiken.toml
# TODO custom prefix set by funder
STT_PREFIX: str = "election"

def full_stt_name(channel_id: ChannelId) -> bytes:
    id_str = channel_id_to_string(channel_id)
    full_str = STT_PREFIX + '-' + id_str
    # return coerce_channel_id(full_str)
    return full_str.encode('utf-8')

# TODO where should this live?
def mint_channel_stt_assets(
        policy_id: ScriptHash,
        n_to_mint: int,
        channel_ids: list[ChannelId]
    ) -> MultiAsset:
    '''Mint or burn (with negative n_to_mint) one or more channel STTs'''
    # the quicker from_primitive way has some normalize error here
    asset = Asset()
    for channel_id in channel_ids:
        stt = AssetName(full_stt_name(channel_id))
        asset[stt] = n_to_mint
    assets = MultiAsset()
    assets[policy_id] = asset
    return assets
