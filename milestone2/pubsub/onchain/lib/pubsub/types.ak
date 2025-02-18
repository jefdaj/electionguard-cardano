use aiken/crypto.{VerificationKeyHash}

// TODO can we restrict these to a particular size or format?
pub type CID  = ByteArray // IPFS content identifier

pub type PubsubDatum {
  publisher: VerificationKeyHash
}

pub type PubsubAction {
  PsOpen                        // open the channel
  PsFund                        // add (or remove) ADA for publishing fees
  PsPublish { cids: List<CID> } // announce publication of the corresponding files
  PsClose                       // close the channel and recover remaining ADA
}
