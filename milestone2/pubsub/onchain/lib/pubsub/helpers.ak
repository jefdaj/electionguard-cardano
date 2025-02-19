use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/transaction.{Transaction}

pub fn signed(tx: Transaction, signer: VerificationKeyHash) -> Bool {
  list.has(tx.extra_signatories, signer)
}
