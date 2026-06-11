# Should be kept in sync with onchain/validators/election/cid.ak

import dataclasses
from multiformats_cid import make_cid
from pydantic.v1 import validator

IpfsCid = bytes
from dataclasses import dataclass, fields as dc_fields
from multiformats_cid import make_cid
from pycardano import PlutusData


# CID Structure: [version(1)][codec(1)][hash_type(1)][hash_length(1)][hash(32)]
# Expected:      0x01        0x55       0x12          0x20             [32-byte SHA-256]
_CID_PREFIX = bytes([0x01, 0x55, 0x12, 0x20])
_CID_LENGTH = 36

# Field names across PlutusData types that should be treated as IPFS CIDs.
IPFS_CID_FIELDS = frozenset({'ipfs_cid'})


def _validate_cid_bytes(b: bytes) -> None:
    """Validate raw CID bytes match CIDv1 / raw / SHA-256 / 32-byte layout."""
    if len(b) != _CID_LENGTH:
        raise ValueError(f"CID must be exactly {_CID_LENGTH} bytes, got {len(b)}")
    if b[0] != 0x01:
        raise ValueError(f"Must be CIDv1, got version {b[0]:#x}")
    if b[1] != 0x55:
        raise ValueError(f"Must use raw codec (0x55), got {b[1]:#x}")
    if b[2] != 0x12:
        raise ValueError(f"Must use SHA-256 hash type (0x12), got {b[2]:#x}")
    if b[3] != 0x20:
        raise ValueError(f"Must use 32-byte hash length (0x20), got {b[3]:#x}")


def coerce_ipfs_cid(value: str | bytes) -> bytes:
    """
    Accept a CID as either its base32 string form or its raw 36-byte form,
    validate it as CIDv1/raw/SHA-256, and return the canonical bytes.
    """
    if isinstance(value, str):
        b = make_cid(value).buffer
    elif isinstance(value, (bytes, bytearray)):
        b = bytes(value)
    else:
        raise TypeError(
            f"ipfs_cid must be str or bytes, got {type(value).__name__}"
        )
    _validate_cid_bytes(b)
    return b


def ipfs_cid_to_string(value: bytes) -> str:
    """Convert canonical CID bytes to their base32 string form."""
    _validate_cid_bytes(value)
    return str(make_cid(value))


class IpfsCidMixin:
    """
    Mixin for PlutusData subclasses that have one or more IPFS CID fields.
    Coerces str -> bytes and validates CIDv1/raw/SHA-256 in __post_init__.

    Must come BEFORE PlutusData in the MRO.
    """

    def __post_init__(self):
        for field_name in IPFS_CID_FIELDS:
            if hasattr(self, field_name):
                current = getattr(self, field_name)
                object.__setattr__(self, field_name, coerce_ipfs_cid(current))
        super_post = getattr(super(), '__post_init__', None)
        if super_post is not None:
            super_post()

    def __str__(self) -> str:
        cls_name = type(self).__name__
        parts = []
        for f in dc_fields(self):
            value = getattr(self, f.name)
            if f.name in IPFS_CID_FIELDS and isinstance(value, bytes):
                parts.append(f"{f.name}={ipfs_cid_to_string(value)!r}")
            else:
                parts.append(f"{f.name}={value!r}")
        return f"{cls_name}({', '.join(parts)})"
