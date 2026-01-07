from dataclasses import dataclass
from multiformats_cid import make_cid, CIDv1
from pycardano import PlutusData

@dataclass
class CIDv1(PlutusData):
    """
    Constructs an IPFS CID to match onchain/lib/pubsub/types.ak::CIDv1.
    Note that Kubo currently defaults to v0, but the devs expect to move to v1 "soon",
    so I'm standardizing on it now. I'm also assuming SHA256.

    Examples:
        # From IPFS string
        >>> cid1 = CIDv1.from_string('bafkreif3ndgroyswbk7nts7xroxklqa2xyjijiqil3eiczvhvehep6vdue')

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
        """Validate the raw CID bytes."""
        if len(self.cid) != 36:
            raise ValueError(f"CIDv1 must be exactly 36 bytes, got {len(self.cid)}")

        if self.cid[0] != 0x01:
            raise ValueError(f"Must be CIDv1, got version {self.cid[0]:#x}")

        if self.cid[2] != 0x12 or self.cid[3] != 0x20:
            raise ValueError(f"Must use SHA-256, got hash type {self.cid[2]:#x} length {self.cid[3]:#x}")

    @classmethod
    def from_string(cls, cid_string: str) -> 'CIDv1':
        """Parse a CID from its string representation."""
        c = make_cid(cid_string)
        return cls(cid=c.buffer)

    def to_string(self) -> str:
        """Convert to base32 string representation."""
        c = make_cid(self.cid)
        return str(c)
