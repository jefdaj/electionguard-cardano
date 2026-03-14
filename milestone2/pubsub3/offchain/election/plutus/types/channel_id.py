# Should be kept in sync with onchain/election/types/channel_id.ak

import re

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
    def from_string(channel_string: str) -> bytes:
        """Convert ChannelId string to bytes with validation."""
        if not ChannelIdHelper._REGEX.match(channel_string):
            raise ValueError(
                f"Invalid ChannelId: '{channel_string}'. "
                "Must be 'admin' or one of 'guardian', 'device', 'verifier' "
                "followed by a number 1-100."
            )
        return channel_string.encode('utf-8')

    @staticmethod
    def to_string(channel_bytes: bytes) -> str:
        """Convert ChannelId bytes to string."""
        try:
            channel_string = channel_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(f"ChannelId bytes are not valid UTF-8: {channel_bytes.hex()}")
        if not ChannelIdHelper._REGEX.match(channel_string):
            raise ValueError(
                f"Invalid ChannelId: '{channel_string}'. "
                "Must be 'admin' or one of 'guardian', 'device', 'verifier' "
                "followed by a number 1-100."
            )

        return channel_string

    @staticmethod
    def validate(channel_bytes: bytes) -> None:
        """Validate ChannelId format."""
        ChannelIdHelper.to_string(channel_bytes)
