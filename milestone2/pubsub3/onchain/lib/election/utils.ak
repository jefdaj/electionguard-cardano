use aiken/primitive/bytearray
use aiken/collection/dict
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use cardano/transaction.{Transaction, Output}

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
  let policy_tokens = assets.tokens(mint, policy_id)

  when dict.get(policy_tokens, token_name) is {
    None -> amount == 0
    Some(actual_amount) -> actual_amount == amount
  }
}

// tx_mints mapped over a list of token names.
pub fn tx_mints_all(
  tx: Transaction,
  policy_id: PolicyId,
  token_names: List<ByteArray>,
  amount: Int,
) -> Bool {
  list.all(token_names, fn(token_name) {
    tx_mints(tx, policy_id, token_name, amount)
  })
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

// like string.join, but for bytearrays
pub fn bytearray_join(
  bytearrays: List<ByteArray>,
  delimiter: ByteArray,
) -> ByteArray {
  when bytearrays is {
    [] -> #""
    [first, ..rest] ->
      list.foldl(
        rest,
        first,
        fn(acc, item) { bytearray.concat(bytearray.concat(acc, delimiter), item) },
      )
  }
}

// TODO should this be done without script_addr? Seems like policy_id would be enough
// pub fn get_stt_datum(
//   self: Transaction,
//   policy_id: PolicyId,
//   stt_name: ByteArray,
//   script_addr: Address,
// ) -> Option<Data> {
//   when tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1) is {
//     Some(stt_output) ->
//       when stt_output.datum is {
//         InlineDatum(raw_datum) -> Some(raw_datum)
//         _ -> None
//       }
//     None -> None
//   }
// }
