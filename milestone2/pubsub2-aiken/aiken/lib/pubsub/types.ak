use aiken/crypto.{VerificationKeyHash}

/// IPFS content identifier
/// TODO can they be restricted to the proper size or format?
pub type CID = ByteArray

pub type PubsubDatum {

  /// TODO nft: ???,
  /// State NFT uniquely identifying the channel.

  publisher: VerificationKeyHash,
  /// All transactions must be signed by this key.
  /// It could be removed in favor of NFT ownership,
  /// but for the ElectionGuard use case I don't want state
  /// NFTs to be transferrable.

}

pub type PubsubAction {

  PsOpen
  /// Open the channel, minting the state NFT and funding with some ADA.

  PsPublish { cids: List<CID> }
  /// Announce publication of the corresponding IPFS files.

  PsCollect
  /// Collect ADA and/or other tokens sent to the validator.
  /// TODO sending ADA to the contract is always valid, right?

  PsClose
  /// Close the channel, burning the NFT and recovering any ADA.
  /// The publisher can choose whether to collect other tokens here too.
  /// TODO if not, are they basically burned/frozen at the validator address?
  /// TODO should it require exlicitly burning any assets you don't want?

}
