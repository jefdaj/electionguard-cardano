use aiken/builtin
use aiken/collection/list

/// Canonical binary peer ID: the multihash of the ipfs_node's public key.
pub type IpfsPeerId =
  ByteArray

/// A single multiaddr in its binary (packed) encoding.
pub type IpfsMultiaddr =
  ByteArray

/// IpfsNode identity + optional dialing hints.
pub type IpfsNode {
  peer_id: IpfsPeerId,
  addr_hints: List<IpfsMultiaddr>,
}

/// Peer ID = a multihash: [hash_code(1)][digest_len(1)][digest(N)]
// Two common cases:
//   - Ed25519 (identity multihash): 0x00 0x24 [36-byte protobuf-wrapped key] -> 38 bytes
//   - RSA/others (sha2-256):        0x12 0x20 [32-byte digest]               -> 34 bytes
// Keeping this structural rather than fully parsing the varint length.
pub fn validate_peer_id(peer_id: IpfsPeerId) -> Bool {
  trace @"validate_peer_id"
  let length      = builtin.length_of_bytearray(peer_id)
  let hash_code   = builtin.index_bytearray(peer_id, 0)
  let digest_len  = builtin.index_bytearray(peer_id, 1)

  and {
    // total length must match the declared digest length + 2 header bytes
    length == digest_len + 2,
    // accept the two codes we expect to see
    or {
      hash_code == 0x00, // identity (Ed25519 public key inlined)
      hash_code == 0x12, // sha2-256
    },
  }
}

/// Very light multiaddr sanity check: non-empty and within a size bound.
// Real multiaddrs are [varint protocol code][value]... repeated; we don't
// parse that here, we just keep obviously-bad values out of the datum.
pub fn validate_multiaddr(addr: IpfsMultiaddr) -> Bool {
  let length = builtin.length_of_bytearray(addr)
  and {
    length > 0,
    length <= 128,
  }
}

/// Validate the whole ipfs_node field.
pub fn validate_ipfs_node(ipfs_node: IpfsNode) -> Bool {
  trace @"validate_ipfs_node"
  let Publisher { peer_id, addr_hints } = ipfs_node

  and {
    validate_peer_id(peer_id),
    // "zero or more" -> an empty list is fine; list.all is vacuously true
    list.all(addr_hints, validate_multiaddr),
    // optional: cap the number of hints so the datum can't blow up
    list.length(addr_hints) <= 8,
  }
}
