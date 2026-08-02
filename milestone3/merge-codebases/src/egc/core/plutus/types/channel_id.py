import re
from dataclasses import dataclass
from pycardano import PlutusData

# Should be kept in sync with onchain/election/types/channel_id.ak
#
# Valid ChannelIds:
# - "admin"
# - "guardian1" through "guardian100"
# - "device1"   through "device100"
# - "verifier1" through "verifier100"


type ChannelId = bytes

_ROLE_RE = re.compile(
    '^(admin|guardian|device|verifier)$'
)

_CHANNEL_ID_RE = re.compile(
    r'^(admin|(guardian|device|verifier)([1-9]\d?|100))$'
)

# Scalar channel-id field names across PlutusData types.
CHANNEL_ID_FIELDS = frozenset({'channel_id', 'verifier_id'})

# List-of-channel-id field names.
CHANNEL_ID_LIST_FIELDS = frozenset({'channels', 'subchannels'})

# Mirrors the Aiken-side limit (and existing Python validator).
MAX_CHANNELS = 100


def is_valid_role(role: str) -> bool:
    return bool(_ROLE_RE.match(role))


def is_valid_channel_str(ch_str: str) -> bool:
    return bool(_CHANNEL_ID_RE.match(ch_str))


def _invalid_channel_id_msg(s: str) -> str:
    return (
        f"Invalid ChannelId: {s!r}. Must be 'admin' or one of "
        f"'guardian', 'device', 'verifier' followed by a number 1-100."
    )


def coerce_channel_id(value: str | bytes) -> bytes:
    """Accept str or bytes, validate format, return canonical bytes."""
    if isinstance(value, str):
        s = value
        b = value.encode('utf-8')
    elif isinstance(value, (bytes, bytearray)):
        b = bytes(value)
        try:
            s = b.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ValueError(
                f"ChannelId bytes are not valid UTF-8: {b.hex()}"
            ) from e
    else:
        raise TypeError(
            f"channel id must be str or bytes, got {type(value).__name__}"
        )

    if not _CHANNEL_ID_RE.match(s):
        raise ValueError(_invalid_channel_id_msg(s))
    return b


def channel_id_to_string(value: bytes) -> str:
    """Decode and validate a channel-id bytes value."""
    try:
        s = value.decode('utf-8')
    except UnicodeDecodeError as e:
        raise ValueError(
            f"ChannelId bytes are not valid UTF-8: {value.hex()}"
        ) from e
    if not _CHANNEL_ID_RE.match(s):
        raise ValueError(_invalid_channel_id_msg(s))
    return s


def coerce_channel_id_list(values) -> list[bytes]:
    """Coerce each element, then enforce list-level constraints."""
    if not isinstance(values, (list, tuple)):
        raise TypeError(
            f"channels must be a list, got {type(values).__name__}"
        )
    coerced = [coerce_channel_id(v) for v in values]
    if len(coerced) > MAX_CHANNELS:
        raise ValueError(f"Too many channels: {len(coerced)} (max {MAX_CHANNELS})")
    if len(coerced) != len(set(coerced)):
        raise ValueError("channels list contains duplicates")
    return coerced


class ChannelIdMixin:
    """
    Mixin for PlutusData subclasses with channel-id fields (scalar or list).
    Coerces str -> bytes and validates format in __post_init__.

    Must come BEFORE PlutusData in the MRO.
    """

    def __post_init__(self):
        for field_name in CHANNEL_ID_FIELDS:
            if hasattr(self, field_name):
                current = getattr(self, field_name)
                object.__setattr__(self, field_name, coerce_channel_id(current))

        for field_name in CHANNEL_ID_LIST_FIELDS:
            if hasattr(self, field_name):
                current = getattr(self, field_name)
                object.__setattr__(self, field_name, coerce_channel_id_list(current))

        super_post = getattr(super(), '__post_init__', None)
        if super_post is not None:
            super_post()


# Module-level constant, kept for backward compatibility with existing call sites.
ADMIN_CHANNEL_ID = coerce_channel_id('admin')

