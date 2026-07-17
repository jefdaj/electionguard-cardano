use aiken/collection/list
use cardano/transaction.{Input, Output}
use cardano/address.{Script}


pub fn are_disjoint(list1: List<a>, list2: List<a>) -> Bool {
  trace @"are_disjoint"
  !list.any(list1, fn(x) { list.has(list2, x) })
}

/// Check if all elements from `subset` are found in `superset`
// pub fn is_subset(subset: List<a>, superset: List<a>) -> Bool {
// list.all(subset, fn(element) { list.has(superset, element) })
// }

/// Remove all occurrences of elements in `to_remove` from `source`
pub fn remove_elements(source: List<a>, to_remove: List<a>) -> List<a> {
  trace @"remove_elements"
  list.filter(source, fn(item) { !list.has(to_remove, item) })
}

pub fn inputs_from_script(
  inputs: List<Input>,
  script_hash: ByteArray,
) -> List<Input> {
  list.filter(
    inputs,
    fn(input) {
      when input.output.address.payment_credential is {
        Script(hash) -> hash == script_hash
        _ -> False
      }
    },
  )
}
