use aiken/collection/list
use election/types/ipfs_cid.{IpfsCid, validate_ipfs_cid}
use tests/data/static_election_records as sr

test all_static_election_cids_valid() {
  let cids: List<IpfsCid> =
    list.map(sr.all_records, fn(r) { r.ipfs_cid })
  list.all(cids, validate_ipfs_cid)
}

/// Test a valid CIDv1 with SHA-256
test valid_cid_test() {
  // Create a valid CIDv1: version(0x01) + codec(0x55) + hash_type(0x12) + length(0x20) + 32-byte hash
  let valid_cid = #"015512200123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  validate_ipfs_cid(valid_cid) == True
}

/// Test another valid CIDv1 with different hash content
test valid_cid_different_hash_test() {
  let valid_cid = #"01551220ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  validate_ipfs_cid(valid_cid) == True
}

/// Test valid CIDv1 with all zeros hash
test valid_cid_zeros_test() {
  let valid_cid = #"015512200000000000000000000000000000000000000000000000000000000000000000"
  validate_ipfs_cid(valid_cid) == True
}

/// Test invalid: wrong length (too short)
test invalid_length_short_test() {
  let invalid_cid = #"0155122001234567"  // Only 8 bytes instead of 36
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: wrong length (too long)
test invalid_length_long_test() {
  let invalid_cid = #"015512200123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef00"  // 37 bytes
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: wrong version (CIDv0)
test invalid_version_v0_test() {
  let invalid_cid = #"005512200123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: wrong version (CIDv2)
test invalid_version_v2_test() {
  let invalid_cid = #"025512200123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: wrong hash type (not SHA-256)
test invalid_hash_type_test() {
  // 0x13 is SHA-512 instead of 0x12 (SHA-256)
  let invalid_cid = #"015513200123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: wrong hash length declaration
test invalid_hash_length_declaration_test() {
  // Says 0x10 (16 bytes) but we expect 0x20 (32 bytes)
  let invalid_cid = #"015512100123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: empty ByteArray
test invalid_empty_cid_test() {
  let invalid_cid = #"" 
  validate_ipfs_cid(invalid_cid) == False
}

/// Test invalid: correct length but wrong codec byte
test invalid_codec_test() {
  // Changed codec from 0x55 (raw) to 0x71 (dag-cbor)
  // Note we may want to switch to 0x71 later for CBOR encoding
  let invalid_cid = #"017112200123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  validate_ipfs_cid(invalid_cid) == False
}

/// Test edge case: minimum valid values
test valid_cid_min_values_test() {
  let valid_cid = #"015512200000000000000000000000000000000000000000000000000000000000000000"
  validate_ipfs_cid(valid_cid) == True
}

/// Test edge case: maximum hash values with valid header
test valid_cid_max_hash_test() {
  let valid_cid = #"01551220ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  validate_ipfs_cid(valid_cid) == True
}
