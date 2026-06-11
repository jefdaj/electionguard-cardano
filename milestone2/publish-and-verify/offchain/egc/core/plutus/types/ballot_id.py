import re
from dataclasses import dataclass
from pycardano import PlutusData

# Should be kept in sync with onchain/validators/election/types/ballot_id.ak

type BallotId = bytes

_BALLOT_ID_RE = re.compile(
    r'^ballot-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)


# Field names that should be treated as ballot IDs in PlutusData types.
BALLOT_ID_FIELDS = frozenset({'ballot_id', 'spoiled_id'})


def coerce_ballot_id(value: str | bytes) -> bytes:
    """Accept str or bytes, validate format, return bytes."""
    if isinstance(value, str):
        s = value
        b = value.encode('utf-8')
    elif isinstance(value, bytes):
        try:
            s = value.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ValueError(f"ballot id must be valid UTF-8: {e}") from e
        b = value
    else:
        raise TypeError(
            f"ballot id must be str or bytes, got {type(value).__name__}"
        )

    if not _BALLOT_ID_RE.match(s):
        raise ValueError(f"Invalid ballot ID format: {s!r}")
    return b


def ballot_id_to_string(value: bytes) -> str:
    """Decode and validate a ballot-id bytes value."""
    s = value.decode('utf-8')
    if not _BALLOT_ID_RE.match(s):
        raise ValueError(f"Decoded ballot ID has invalid format: {s!r}")
    return s


class BallotIdMixin:
    """
    Mixin for PlutusData subclasses that have one or more ballot-id fields.
    Coerces str -> bytes and validates format in __post_init__.

    Must come BEFORE PlutusData in the MRO so this __post_init__ runs.
    """

    def __post_init__(self):
        for field_name in BALLOT_ID_FIELDS:
            if hasattr(self, field_name):
                current = getattr(self, field_name)
                object.__setattr__(self, field_name, coerce_ballot_id(current))
        # Chain to PlutusData's __post_init__ if it has one
        super_post = getattr(super(), '__post_init__', None)
        if super_post is not None:
            super_post()
