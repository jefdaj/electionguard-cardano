use aiken/collection/list
use aiken/builtin
use aiken/crypto.{VerificationKeyHash}

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
  let hash_type   = builtin.index_bytearray(cid, 2)
  let hash_length = builtin.index_bytearray(cid, 3)
  and {
    length      == 36,
    version     == 0x01, // CIDv1
    hash_type   == 0x12, // SHA-256
    hash_length == 0x20  // 32 bytes
  }
}

/// Validate a list of CIDs
pub fn validate_cids(cids: List<CIDv1>) -> Bool {
  trace @"validate_cids"
  list.all(cids, validate_cid)
}

// TODO set my kubo containers to use v1:
//      ipfs config --json Import.CidVersion 1
//      ipfs add --cid-version=1 myfile.txt

pub type PubsubConfig {
  // All transactions must be signed by the publisher's key.
  // TODO allow the channel to be created by a separate admin
  publisher: VerificationKeyHash,
}

pub type PubsubAction {

  /// Open the channel, minting the STT and funding with min ADA.
  // TODO also send extra ADA to pay publishing fees?
  PsOpen

  /// Announce publication of the corresponding IPFS files.
  PsPublish { cids: List<CIDv1> }

  // Collect ADA and/or other tokens sent to the validator.
  // TODO sending ADA to the contract is always valid, right?
  // PsCollect

  /// Close the channel, burning the STT and recovering any ADA.
  /// The publisher can choose whether to collect other tokens here too.
  // TODO if not, are they basically burned/frozen at the validator address?
  // TODO should it require exlicitly burning any assets you don't want?
  PsClose
}
