from multiformats_cid import make_cid, CIDv1

# TODO remove this? doesn't seem that helpful now, but a class will be needed for JSON msgs later
class CIDv1:
    """
    Helper class for IPFS CIDv1 operations.

    Constructs an IPFS CID to match onchain/lib/pubsub/types.ak::CIDv1.
    Note that Kubo currently defaults to v0, but the devs expect to move to v1 "soon",
    so I'm standardizing on it now. I'm also assuming SHA256.

    Examples:
        # From IPFS string
        >>> cid1 = CIDv1.from_string('bafkreif3ndgroyswbk7nts7xroxklqa2xyjijiqil3eiczvhvehep6vdue')

        # Convert back to string for IPFS operations
        >>> ipfs_hash = cid1.to_string()

        # Use with aioipfs
        >>> async with aioipfs.AsyncIPFS() as client:
        >>>     content = await client.cat(cid1.to_string())
    """

    @staticmethod
    def from_string(cid_string: str) -> bytes:
        """Parse a CID from its string representation."""
        c = make_cid(cid_string)
        buffer = c.buffer

        # Validate
        if len(buffer) != 36:
            raise ValueError(f"CIDv1 must be exactly 36 bytes, got {len(buffer)}")
        if buffer[0] != 0x01:
            raise ValueError(f"Must be CIDv1, got version {buffer[0]:#x}")
        if buffer[2] != 0x12 or buffer[3] != 0x20:
            raise ValueError(f"Must use SHA-256")

        return buffer

    @staticmethod
    def to_string(cid_bytes: bytes) -> str:
        """Convert to base32 string representation."""
        c = make_cid(cid_bytes)
        return str(c)
