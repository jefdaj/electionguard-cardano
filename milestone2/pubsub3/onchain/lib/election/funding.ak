use aiken/collection/list
use cardano/transaction.{Transaction, Input}
use cardano/assets.{PolicyId, Value, lovelace_of, policies}

/// Checks that the channel's ADA is preserved minus transaction fees.
/// Allows external contributions and change outputs.
pub fn channel_ada_preserved(
  tx: Transaction,
  policy_id: PolicyId,
) -> Bool {
  let channel_input_ada  =  ada_in_inputs_with_policy(tx, policy_id)
  let channel_output_ada = ada_in_outputs_with_policy(tx, policy_id)
  channel_output_ada + tx.fee >= channel_input_ada
}

/// Calculates total ADA in inputs that contain tokens from the policy
fn ada_in_inputs_with_policy(
  // inputs: List<Input>,
  tx: Transaction,
  policy_id: PolicyId,
) -> Int {
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
fn has_policy(val: Value, policy_id: PolicyId) -> Bool {
  list.has(policies(val), policy_id)
}
