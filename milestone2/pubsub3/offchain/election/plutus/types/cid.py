# Should be kept in sync with onchain/validators/election/cid.ak

from multiformats_cid import make_cid

CID = bytes

class CIDHelper:
    """
    Helper class for IPFS CID operations.

    CIDs are just ByteArrays on chain, but try to use this class for any/all
    conversions to keep their formats correct. It should also be kept in sync
    with: onchain/validators/election/cid.ak

    Note that Kubo currently defaults to v0, but the devs expect to move to v1 "soon",
    so I'm standardizing on it now. I'm also assuming SHA256 with raw codec, but may
    switch to CBOR or JSON later.

    CID Structure: [version(1)][codec(1)][hash_type(1)][hash_length(1)][hash(32)]
    Expected: 0x01 0x55 0x12 0x20 [32-byte SHA-256]

    Examples:
        # From IPFS string
        >>> cid_bytes = CIDHelper.from_string('bafkreif3ndgroyswbk7nts7xroxklqa2xyjijiqil3eiczvhvehep6vdue')

        # Use in PlutusData
        >>> record = PublicRecord(cid=cid_bytes, metadata=Manifest())

        # Convert back to string for IPFS operations
        >>> ipfs_hash = CIDHelper.to_string(cid_bytes)

        # Use with aioipfs
        >>> async with aioipfs.AsyncIPFS() as client:
        >>>     content = await client.cat(CIDHelper.to_string(cid_bytes))
    """

    @staticmethod
    def from_string(cid_string: str) -> CID:
        """Parse a CID from its string representation and validate it's a CIDv1 with SHA-256 and raw codec."""
        c = make_cid(cid_string)
        buffer = c.buffer

        # Validate to match Aiken's validate_cid
        if len(buffer) != 36:
            raise ValueError(f"CID must be exactly 36 bytes, got {len(buffer)}")
        if buffer[0] != 0x01:
            raise ValueError(f"Must be CID, got version {buffer[0]:#x}")
        if buffer[1] != 0x55:
            raise ValueError(f"Must use raw codec (0x55), got {buffer[1]:#x}")
        if buffer[2] != 0x12:
            raise ValueError(f"Must use SHA-256 hash type (0x12), got {buffer[2]:#x}")
        if buffer[3] != 0x20:
            raise ValueError(f"Must use 32-byte hash length (0x20), got {buffer[3]:#x}")

        return buffer

    @staticmethod
    def to_string(cid_bytes: CID) -> str:
        """Convert CID bytes to base32 string representation."""
        c = make_cid(cid_bytes)
        return str(c)

    @staticmethod
    def validate(cid_bytes: CID) -> None:
        """Validate that bytes represent a valid CIDv1 with SHA-256 and raw codec."""
        if len(cid_bytes) != 36:
            raise ValueError(f"CIDv1 must be exactly 36 bytes, got {len(cid_bytes)}")
        if cid_bytes[0] != 0x01:
            raise ValueError(f"Must be CIDv1, got version {cid_bytes[0]:#x}")
        if cid_bytes[1] != 0x55:
            raise ValueError(f"Must use raw codec (0x55), got {cid_bytes[1]:#x}")
        if cid_bytes[2] != 0x12:
            raise ValueError(f"Must use SHA-256 hash type (0x12), got {cid_bytes[2]:#x}")
        if cid_bytes[3] != 0x20:
            raise ValueError(f"Must use 32-byte hash length (0x20), got {cid_bytes[3]:#x}")
