from dataclasses import dataclass
from multiformats_cid import make_cid, CIDv1
from pycardano import PlutusData

@dataclass
class CIDv1(PlutusData):
    """
    Constructs an IPFS CID to match onchain/lib/pubsub/types.ak::CIDv1.
    Note that Kubo currently defaults to v0, but the devs expect to move to v1 "soon",
    so I'm telling all the relevant containers to use it now.

    Examples:
        # From IPFS string
        >>> cid1 = CIDv1.from_string('TODO fill in')

        # From raw bytes (e.g., from chain)
        >>> cid2 = CIDv1(cid=bytes_from_datum)

        # Convert back to string for IPFS operations
        >>> ipfs_hash = cid1.to_string()

        # Use with aioipfs
        >>> async with aioipfs.AsyncIPFS() as client:
        >>>     content = await client.cat(cid1.to_string())
    """

    cid: bytes

    def __post_init__(self):
        """Validate the raw CIDv1 bytes."""
        if len(self.cid) != 36:
            raise ValueError(f"CIDv1 must be exactly 36 bytes, got {len(self.cid)}")
        if self.cid[0] != 0x01:
            raise ValueError("Must be CIDv1")
        if self.cid[2] != 0x12 or self.cid[3] != 0x20:
            raise ValueError("Must use SHA-256")

    @classmethod
    def from_string(cls, cid_string: str) -> 'CIDv1':
        """Parse a CIDv1 from its string representation."""
        c = make_cid(cid_string)
        return cls(cid=c.encode())  # .encode() gives raw bytes

    def to_string(self) -> str:
        """Convert to base32 string representation."""
        c = make_cid(self.cid)
        return str(c)  # Returns base32 by default for CIDv1

    @classmethod
    def from_multihash(cls, multihash: bytes, codec: str = 'dag-pb') -> 'CIDv1':
        """Create a CIDv1 from a multihash and codec."""
        c = CIDv1(codec, multihash)
        return cls(cid=c.encode())

@dataclass
class PubsubAction(PlutusData):
    "Superclass to use as a union type"

@dataclass
class PsOpen(PubsubAction):
    """
    Examples:
        >>> open_action = PsOpen()
    """
    CONSTR_ID = 0

# TODO put back after building out the test framework with just open + close
# @dataclass
# class PsPublish(PubsubAction):
#     """
#     Examples:
#         >>> publish_action = PubsubAction.ps_publish([b'cid1', b'cid2'])
#     """
#     CONSTR_ID = 1
#     cids: List[CIDv1]

# TODO remove?
# @dataclass
# class PsCollect(PubsubAction):
#     CONSTR_ID = 2

@dataclass
class PsClose(PubsubAction):
    """
    Examples:
        >>> close_action = PsClose()
    """
    CONSTR_ID = 1 # TODO will be 2 once PsPublish is added
