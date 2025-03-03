use aiken/crypto.{VerificationKeyHash}

/// ipfs content identifier
/// TODO can we restrict these to a particular size or format?
pub type CID =
  ByteArray

pub type PubsubDatum {
  publisher: VerificationKeyHash,
}

pub type PubsubAction {

  PsOpen
  /// open the channel

  PsPublish { cids: List<CID> }
  /// announce publication of the corresponding files

  PsCollect
  /// collect ada and/or other tokens sent to the validator addr
  /// TODO sending ada to the contract is always valid, right?

  PsClose
  /// close the channel and recover remaining ada
  /// TODO should this require exlicitly burning any assets you don't want?

}
