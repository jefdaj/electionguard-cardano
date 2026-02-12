use aiken/collection/dict
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use cardano/transaction.{Transaction, Input, Output, OutputReference}

// Whether a transaction was signed by the required key.
pub fn tx_signed_by(tx: Transaction, signer: VerificationKeyHash) -> Bool {
  list.has(tx.extra_signatories, signer)
}

// Whether a transaction consumes (includes as input) the required oref.
// TODO is this redundant with transaction.find_input?
pub fn find_tx_input(tx: Transaction, oref: OutputReference) -> Option<Input> {
  let Transaction { inputs, .. } = tx
  list.find(inputs, fn(i) { i.output_reference == oref })
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

// TODO name something better
// TODO implement in terms of tx_mints?
pub fn tx_does_not_mint(
  tx: Transaction,
  policy_id: PolicyId
) -> Bool {
  let Transaction { mint, .. } = tx
  let minted = mint |> assets.tokens(policy_id) |> dict.to_pairs()
  minted == []
}

// From Rhys's Aiken Language Test Lib 3/5 video
pub fn scriptAddress(hash: ByteArray) -> Address {
  let addr = Address {
    payment_credential: Script(hash),
    stake_credential: None,
  }
  addr
}

pub fn tx_sends_token_to_addr(
  tx: Transaction,
  policy_id: PolicyId,
  token_name: ByteArray,
  addr: Address,
  min_quantity: Int // TODO require exact quantity?
) -> Option<Output> {
  tx.outputs
  |> list.find(fn(output) {
       output.address == addr &&
       assets.quantity_of(output.value, policy_id, token_name) >= min_quantity
     })
}
