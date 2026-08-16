from dataclasses import dataclass, fields as dc_fields
from typing import List, Union

import re
import base58
from multiaddr import Multiaddr as _MultiaddrObj
from pycardano import PlutusData

from .action import decode_plutusdata_union

# Should be kept in sync with onchain/validators/election/types/ipfs_node.ak


type IpfsPeerId = bytes
type IpfsMultiaddr = bytes

# Peer ID = multihash: [hash_code(1)][digest_len(1)][digest(N)]
#   - 0x00 identity  (Ed25519 public key inlined): 0x00 0x24 + 36 bytes -> 38
#   - 0x12 sha2-256                              : 0x12 0x20 + 32 bytes -> 34
_PEER_ID_HASH_CODES = frozenset({0x00, 0x12})

# Multiaddr / hint-list bounds (mirror the on-chain guards).
_MAX_MULTIADDR_LEN = 128
_MAX_ADDR_HINTS = 8

# Field names across PlutusData types that should be treated as peer IDs
# (scalar bytes) and as multiaddr hint lists (List[bytes]), respectively.
PEER_ID_FIELDS = frozenset({'peer_id'})
MULTIADDR_FIELDS = frozenset({'addr_hints'})


# --------------------------------------------------------------------------
# peer id
# --------------------------------------------------------------------------

def _validate_peerid_bytes(b: bytes) -> None:
    """Validate raw peer-id bytes as a well-formed (single-byte-length) multihash."""
    if len(b) < 2:
        raise ValueError(f"peer_id must be at least 2 bytes, got {len(b)}")
    hash_code = b[0]
    digest_len = b[1]
    if hash_code not in _PEER_ID_HASH_CODES:
        raise ValueError(
            f"peer_id hash code must be one of "
            f"{{{', '.join(hex(c) for c in sorted(_PEER_ID_HASH_CODES))}}}, "
            f"got {hash_code:#x}"
        )
    if len(b) != digest_len + 2:
        raise ValueError(
            f"peer_id length mismatch: header claims {digest_len} digest bytes "
            f"(expected total {digest_len + 2}), got {len(b)}"
        )


def coerce_ipfs_peerid(value: Union[str, bytes, bytearray]) -> bytes:
    """
    Accept a peer ID as either its base58btc string form (e.g. 'Qm...' / '12D3Koo...')
    or its raw multihash bytes, validate it, and return the canonical bytes.
    """
    if isinstance(value, str):
        b = base58.b58decode(value)
    elif isinstance(value, (bytes, bytearray)):
        b = bytes(value)
    else:
        raise TypeError(
            f"peer_id must be str or bytes, got {type(value).__name__}"
        )
    _validate_peerid_bytes(b)
    return b


def ipfs_peerid_to_string(value: bytes) -> str:
    """Convert canonical peer-id bytes to their base58btc string form."""
    _validate_peerid_bytes(value)
    return base58.b58encode(value).decode("ascii")


# --------------------------------------------------------------------------
# multiaddr
# --------------------------------------------------------------------------

def _validate_multiaddr_bytes(b: bytes) -> None:
    """Light structural check matching the on-chain non-empty + size guard."""
    if len(b) == 0:
        raise ValueError("multiaddr must be non-empty")
    if len(b) > _MAX_MULTIADDR_LEN:
        raise ValueError(
            f"multiaddr must be <= {_MAX_MULTIADDR_LEN} bytes, got {len(b)}"
        )


def coerce_ipfs_multiaddr(value: Union[str, bytes, bytearray]) -> bytes:
    """
    Accept a multiaddr as either its human string form
    (e.g. '/ip4/1.2.3.4/tcp/4001') or its packed bytes, and return canonical bytes.
    """
    if isinstance(value, str):
        value = re.sub('^r:', '', value) # TODO clean this up!
        b = _MultiaddrObj(value).to_bytes()
    elif isinstance(value, (bytes, bytearray)):
        # round-trip through the parser to reject obvious garbage
        b = _MultiaddrObj(bytes(value)).to_bytes()
    else:
        raise TypeError(
            f"multiaddr must be str or bytes, got {type(value).__name__}"
        )
    _validate_multiaddr_bytes(b)
    return b


def ipfs_multiaddr_to_string(value: bytes) -> str:
    """Convert packed multiaddr bytes to their human string form."""
    _validate_multiaddr_bytes(value)
    s = str(_MultiaddrObj(value))
    if '/p2p/' in s:
        s = 'r:' + s # TODO clean this up!
    return s


# --------------------------------------------------------------------------
# mixins
# --------------------------------------------------------------------------

# TODO move to util class and use for other str fields too?
class _PlutusStrMixin:
    """
    Shared field-aware __str__. Cooperating mixins register per-field
    formatters by overriding _field_formatters() and merging via super().
    Must come (indirectly) BEFORE PlutusData in the MRO.
    """

    def _field_formatters(self) -> dict:
        parent = getattr(super(), '_field_formatters', None)
        return dict(parent()) if parent is not None else {}

    def __str__(self) -> str:
        formatters = self._field_formatters()
        parts = []
        for f in dc_fields(self):
            value = getattr(self, f.name)
            fmt = formatters.get(f.name)
            parts.append(f"{f.name}={fmt(value) if fmt else repr(value)}")
        return f"{type(self).__name__}({', '.join(parts)})"


class IpfsPeerIdMixin(_PlutusStrMixin):
    """
    Mixin for PlutusData subclasses with one or more peer-id fields (scalar bytes).
    Coerces str -> bytes and validates the multihash shape in __post_init__.

    Must come BEFORE PlutusData in the MRO.
    """

    def __post_init__(self):
        for name in PEER_ID_FIELDS:
            if hasattr(self, name):
                object.__setattr__(self, name, coerce_ipfs_peerid(getattr(self, name)))
        super_post = getattr(super(), '__post_init__', None)
        if super_post is not None:
            super_post()

    def _field_formatters(self) -> dict:
        fmts = super()._field_formatters()
        for name in PEER_ID_FIELDS:
            fmts[name] = lambda v: repr(ipfs_peerid_to_string(v))
        return fmts


class IpfsMultiaddrMixin(_PlutusStrMixin):
    """
    Mixin for PlutusData subclasses with one or more multiaddr hint-list fields
    (List[bytes]). Coerces each element str -> bytes, validates it, and enforces
    the per-list count cap in __post_init__.

    Must come BEFORE PlutusData in the MRO.
    """

    def __post_init__(self):
        for name in MULTIADDR_FIELDS:
            if hasattr(self, name):
                hints = [coerce_ipfs_multiaddr(a) for a in getattr(self, name)]
                if len(hints) > _MAX_ADDR_HINTS:
                    raise ValueError(
                        f"{name}: at most {_MAX_ADDR_HINTS} entries allowed, "
                        f"got {len(hints)}"
                    )
                object.__setattr__(self, name, hints)
        super_post = getattr(super(), '__post_init__', None)
        if super_post is not None:
            super_post()

    def _field_formatters(self) -> dict:
        fmts = super()._field_formatters()
        for name in MULTIADDR_FIELDS:
            fmts[name] = lambda v: repr([ipfs_multiaddr_to_string(a) for a in v])
        return fmts


# --------------------------------------------------------------------------
# IpfsNode PlutusData
# --------------------------------------------------------------------------

@dataclass
class IpfsNode(IpfsPeerIdMixin, IpfsMultiaddrMixin, PlutusData):
    """
    Publisher identity + optional dialing hints.

    Mirrors the on-chain type:
        pub type IpfsNode {
          peer_id: IpfsPeerId,
          addr_hints: List<IpfsMultiaddr>,
        }
    """

    CONSTR_ID = 0

    peer_id: bytes
    addr_hints: List[bytes]


# --------------------------------------------------------------------------
# Option<IpfsNode>
# --------------------------------------------------------------------------

# TODO make this generic and re-use for other types?
# TODO anything needed for proper __str__?
# TODO Some comes before None?

@dataclass
class SomeIpfsNode(PlutusData):
    """Aiken: Some(IpfsNode)"""
    CONSTR_ID = 0
    value: IpfsNode

    def __str__(self) -> str:
        return f'SomeIpfsNode(value={str(self.value)})'

@dataclass
class NoIpfsNode(PlutusData):
    """Aiken: None"""
    CONSTR_ID = 1

OptionIpfsNode = Union[SomeIpfsNode, NoIpfsNode]

def decode_option_ipfs_node(redeemer_str):
    return decode_plutusdata_union(OptionIpfsNode, redeemer_str)
