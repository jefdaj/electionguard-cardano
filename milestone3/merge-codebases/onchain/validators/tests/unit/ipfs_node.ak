use election/types/ipfs_node.{
  IpfsNode,
  validate_peer_id, validate_multiaddr,
  validate_ipfs_node
}

// ---- validate_peer_id ----

test peer_id_valid_ed25519() {
  // 0x00 identity, 0x24 = 36-byte digest, then 36 bytes -> total 38
  let pid =
    #"0024aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  validate_peer_id(pid)
}

test peer_id_valid_sha256() {
  // 0x12 sha2-256, 0x20 = 32-byte digest, then 32 bytes -> total 34
  let pid =
    #"1220bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  validate_peer_id(pid)
}

test peer_id_wrong_hash_code() {
  // hash_code 0x01 is not accepted (length is otherwise consistent: 34)
  let pid =
    #"0120bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  validate_peer_id(pid) == False
}

test peer_id_length_mismatch() {
  // claims 0x20 (32) bytes but only 28 follow -> length 30, expected 34
  let pid = #"1220bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  validate_peer_id(pid) == False
}

test peer_id_empty() {
  validate_peer_id(#"") == False
}

test peer_id_one_byte() {
  validate_peer_id(#"12") == False
}

// ---- validate_multiaddr ----

test multiaddr_valid() {
  // roughly /ip4/1.2.3.4/tcp/4001 in binary-ish form; shape doesn't matter here
  validate_multiaddr(#"0401020304060fa1")
}

test multiaddr_empty() {
  validate_multiaddr(#"") == False
}

test multiaddr_too_long() {
  // 129 bytes -> exceeds the 128 cap
  let addr =
    #"00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00"
  validate_multiaddr(addr) == False
}

// ---- validate_ipfs_node ----

test publisher_valid_no_hints() {
  let p =
    IpfsNode {
      peer_id: #"1220bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      addr_hints: [],
    }
  validate_ipfs_node(p)
}

test publisher_valid_with_hints() {
  let p =
    IpfsNode {
      peer_id: #"1220bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      addr_hints: [#"0401020304060fa1", #"04ac1100010600fb"],
    }
  validate_ipfs_node(p)
}

test publisher_bad_peer_id() {
  let p =
    IpfsNode {
      peer_id: #"0120bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      addr_hints: [],
    }
  validate_ipfs_node(p) == False
}

test publisher_bad_hint() {
  let p =
    IpfsNode {
      peer_id: #"1220bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      addr_hints: [#"0401020304060fa1", #""],  // second hint is empty
    }
  validate_ipfs_node(p) == False
}

test publisher_too_many_hints() {
  let hint = #"0401020304060fa1"
  let p =
    IpfsNode {
      peer_id: #"1220bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      addr_hints: [hint, hint, hint, hint, hint, hint, hint, hint, hint], // 9 > cap of 8
    }
  validate_ipfs_node(p) == False
}
