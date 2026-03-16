use aiken/collection/list
use cardano/transaction.{Transaction, Input, OutputReference}
use cardano/assets.{PolicyId, Value, lovelace_of, policies}

use election/types/action.{ElectionAction, InitElection, EndElection}
use election/stt.{get_policy_id}

// During the election, we want to make sure that no one takes ADA out of
// the channel fee pools, but also allow change from top-up transactions.
// At the end of the election, the admin can send remaining ADA wherever
// they want. In future versions, this would be a good place to add
// treasury logic.
pub fn ada_retained_during_election(
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"ada_retained_during_election"
  when redeemer is {
    InitElection | EndElection -> True
    _ -> {
      let policy_id = get_policy_id(own_ref, tx.inputs)
      script_ada_retained(tx, policy_id)
    }
  }
}

/// Checks that the script controlled ADA is retained minus transaction fees.
/// Allows external contributions and change outputs.
fn script_ada_retained(
  tx: Transaction,
  policy_id: PolicyId,
) -> Bool {
  trace @"script_ada_retained"
  let script_input_ada  =  ada_in_inputs_with_policy(tx, policy_id)
  let script_output_ada = ada_in_outputs_with_policy(tx, policy_id)
  script_output_ada + tx.fee >= script_input_ada
}

/// Calculates total ADA in inputs that contain tokens from the policy
fn ada_in_inputs_with_policy(
  // inputs: List<Input>,
  tx: Transaction,
  policy_id: PolicyId,
) -> Int {
  trace @"ada_in_inputs_with_policy"
  list.foldl(
    tx.inputs,
    0,
    fn(input, acc) {
      if has_policy(input.output.value, policy_id) {
        acc + lovelace_of(input.output.value)
      } else {
        acc
      }
    }
  )
}

/// Calculates total ADA in outputs that contain tokens from the policy
fn ada_in_outputs_with_policy(
  // outputs: List<OutputReference>,
  tx: Transaction,
  policy_id: PolicyId,
) -> Int {
  trace @"ada_in_outputs_with_policy"
  list.foldl(
    tx.outputs,
    0,
    fn(output, acc) {
      if has_policy(output.value, policy_id) {
        acc + lovelace_of(output.value)
      } else {
        acc
      }
    }
  )
}

/// Checks if a value contains any tokens from the specified policy
// TODO there's a specific fn for this, right?
fn has_policy(val: Value, policy_id: PolicyId) -> Bool {
  trace @"has_policy"
  list.has(policies(val), policy_id)
}
