use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/transaction.{Transaction}

// Whether a transaction was signed by the required key.
pub fn tx_signed_by(tx: Transaction, signer: VerificationKeyHash) -> Bool {
  list.has(tx.extra_signatories, signer)
}

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
