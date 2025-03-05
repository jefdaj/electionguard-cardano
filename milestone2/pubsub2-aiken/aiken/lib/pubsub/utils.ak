use aiken/collection/dict
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/assets.{PolicyId}
use cardano/transaction.{Input, OutputReference, Transaction}

// Whether a transaction was signed by the required key.
pub fn tx_signed_by(tx: Transaction, signer: VerificationKeyHash) -> Bool {
  list.has(tx.extra_signatories, signer)
}

// Whether a transaction mints the required amount of a token.
pub fn tx_mints(
  tx: Transaction,
  policy_id: PolicyId,
  token_name: ByteArray,
  amount: Int,
) -> Bool {
  let Transaction { mint, .. } = tx
  expect [Pair(actual_name, actual_amount)] =
    mint
      |> assets.tokens(policy_id)
      |> dict.to_pairs()
  and {
    actual_name == token_name,
    actual_amount == amount,
  }
}
