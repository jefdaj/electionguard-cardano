# Should be kept in sync with onchain/election/types/channel_id.ak

# TODO should this also do the final AssetName wrapping/unwrapping?

import re
from typing import List
from pydantic.v1 import validator

type ChannelId = bytes

class ChannelIdHelper:
    """
    Helper for ChannelId operations.

    This should be doing almost all production conversions, since on chain
    everything is a ByteArray; the channel_id helper in channel_id.ak is mostly
    for use in local `aiken check` tests.

    Valid ChannelIds:
    - "admin"
    - "guardian1" through "guardian100"
    - "device1" through "device100"
    - "verifier1" through "verifier100"

    Examples:
        >>> channel_id = ChannelIdHelper.from_string("admin")
        >>> channel_id = ChannelIdHelper.from_string("guardian5")
        >>> ChannelIdHelper.to_string(channel_id)
        'guardian5'
    """

    _REGEX = re.compile(r'^(admin|(guardian|device|verifier)([1-9]\d?|100))$')

    @staticmethod
    def validate(channel_string: str) -> bool:
        return ChannelIdHelper._REGEX.match(channel_string) is not None

    @staticmethod
    def from_string(channel_string: str) -> bytes:
        if not ChannelIdHelper.validate(channel_string):
            raise ValueError(
                f"Invalid ChannelId: '{channel_string}'. "
                "Must be 'admin' or one of 'guardian', 'device', 'verifier' "
                "followed by a number 1-100."
            )
        return channel_string.encode('utf-8')

    @staticmethod
    def to_string(channel_bytes: bytes) -> str:
        try:
            channel_string = channel_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(
                f"ChannelId bytes are not valid UTF-8: {channel_bytes.hex()}"
            )
        if not ChannelIdHelper.validate(channel_string):
            raise ValueError(
                f"Invalid ChannelId: '{channel_string}'. "
                "Must be 'admin' or one of 'guardian', 'device', 'verifier' "
                "followed by a number 1-100."
            )
        return channel_string

    @staticmethod
    def validate_bytes(channel_bytes: bytes) -> bool:
        try:
            channel_string = channel_bytes.decode('utf-8')
            return ChannelIdHelper.validate(channel_string)
        except UnicodeDecodeError:
            return False

class ChannelIdMixin:
    """Mixin that validates channel_id fields (single or list)."""

    @validator('channel_id', 'verifier_id', allow_reuse=True)
    def validate_channel_id_field(cls, v):
        ChannelIdHelper.to_string(v) # Validates and raises if invalid
        return v

    @validator('channels', 'subchannels', allow_reuse=True, each_item=True)
    def validate_channels_list_items(cls, v):
        ChannelIdHelper.to_string(v) # Validates and raises if invalid
        return v

    @validator('channels', 'subchannels', allow_reuse=True)
    def validate_channels_list_constraints(cls, v):
        if len(v) > 100: # TODO should there be a max?
            raise ValueError(f"Too many channels: {len(v)} (max 100)")
        if len(v) != len(set(v)):
            raise ValueError("channels list contains duplicates")
        return v

ADMIN_CHANNEL_ID = ChannelIdHelper.from_string('admin')
