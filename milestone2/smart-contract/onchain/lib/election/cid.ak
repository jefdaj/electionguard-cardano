use aiken/builtin

/// IPFS content identifier (CID)
// Note that Kubo currently defaults to v0, but the devs expect to move to v1 "soon",
// so I'm telling all the relevant containers to use it now.
pub type CIDv1 =
  ByteArray

/// CIDv1 with SHA-256
// Structure: [version(1)][codec(1)][hash_type(1)][hash_length(1)][hash(32)]
// Common: 0x01 0x70 0x12 0x20 [32-byte SHA-256]
pub fn validate_cid(cid: CIDv1) -> Bool {
  let length  = builtin.length_of_bytearray(cid)
  let version     = builtin.index_bytearray(cid, 0)

  // use dag-pb codec (Kubo default) for now
  // TODO would it make sense to switch to 0x71 (dag-cbor) later?
  let codec       = builtin.index_bytearray(cid, 1)

  let hash_type   = builtin.index_bytearray(cid, 2)
  let hash_length = builtin.index_bytearray(cid, 3)
  and {
    length      == 36,
    version     == 0x01, // CIDv1
    codec       == 0x70, // dag-pb
    hash_type   == 0x12, // SHA-256
    hash_length == 0x20  // 32 bytes
  }
}
