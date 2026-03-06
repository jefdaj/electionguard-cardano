use aiken/primitive/bytearray
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/transaction.{Transaction}

// Whether a transaction was signed by the required key.
pub fn tx_signed_by(tx: Transaction, signer: VerificationKeyHash) -> Bool {
  list.has(tx.extra_signatories, signer)
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

pub fn are_disjoint(list1: List<a>, list2: List<a>) -> Bool {
  !list.any(list1, fn(x) { list.has(list2, x) })
}

/// Check if all elements from `subset` are found in `superset`
// pub fn is_subset(subset: List<a>, superset: List<a>) -> Bool {
// list.all(subset, fn(element) { list.has(superset, element) })
// }

/// Remove all occurrences of elements in `to_remove` from `source`
pub fn remove_elements(source: List<a>, to_remove: List<a>) -> List<a> {
  list.filter(source, fn(item) { !list.has(to_remove, item) })
}
