use aiken/crypto.{VerificationKeyHash}

// TODO set my kubo containers to use v1:
//      ipfs config --json Import.CidVersion 1
//      ipfs add --cid-version=1 myfile.txt

/// IPFS content identifier
// Note that Kubo currently defaults to v0, but the devs expect to move to v1 "soon",
// so I'm telling all the relevant containers to use it now.
pub type CIDv1 =
  ByteArray

pub type PubsubConfig {
  /// TODO nft: ???,
  /// State NFT uniquely identifying the channel.
  /// All transactions must be signed by this key.
  /// It could be removed in favor of tracking NFT ownership,
  /// but for the ElectionGuard use case I don't want state
  /// NFTs to be transferrable.
  publisher: VerificationKeyHash,
}

pub type PubsubAction {

  /// Open the channel, minting the state NFT and funding with some ADA.
  /// TODO is the ADA optional beyond the blockchain-enforced min?
  PsOpen

  /// Announce publication of the corresponding IPFS files.
  // PsPublish { cids: List<CIDv1> }

  /// Collect ADA and/or other tokens sent to the validator.
  /// TODO sending ADA to the contract is always valid, right?
  // PsCollect

  /// Close the channel, burning the NFT and recovering any ADA.
  /// The publisher can choose whether to collect other tokens here too.
  /// TODO if not, are they basically burned/frozen at the validator address?
  /// TODO should it require exlicitly burning any assets you don't want?
  PsClose
}
