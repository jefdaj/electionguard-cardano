use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/address.{VerificationKey}
use cardano/transaction.{NoDatum, Transaction, Input, Output, OutputReference}
use cardano/assets.{PolicyId, Value, lovelace_of, policies}

use election/types/action.{ElectionAction, AddSubChannels, InitElection, EndElection, BurnTestTokens}
use election/stt.{get_policy_id, full_stt_name, get_stt_state}
use election/types/channel_id.{ChannelId}
use election/types/channel.{SubChannel}

// Collateral to be sent to each subchannel publisher.
pub const collateral_lovelace: Int = 5_000_000

// During the election, we want to make sure that no one takes ADA out of the
// channel fee pools, but also allow change from top-up transactions and
// collateral payouts to new publishers. At the end of the election, the admin
// can send remaining ADA wherever they want. In future versions, this would be
// a good place to add treasury logic.
pub fn ada_retained_during_election(
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"ada_retained_during_election"
  when redeemer is {
    BurnTestTokens -> True // TODO remove for production
    InitElection | EndElection -> True
    AddSubChannels { channels } -> {
      let policy_id = get_policy_id(own_ref, tx.inputs)
      let allowance = list.length(channels) * collateral_lovelace
      script_ada_retained(tx, policy_id, allowance)
    }
    _ -> {
      let policy_id = get_policy_id(own_ref, tx.inputs)
      script_ada_retained(tx, policy_id, 0)
    }
  }
}

// Checks that the script controlled ADA is retained minus transaction fees
// and an "allowance" (collateral payouts to new publishers). Allows external
// contributions and change outputs.
fn script_ada_retained(
  tx: Transaction,
  policy_id: PolicyId,
  allowance: Int,
) -> Bool {
  trace @"script_ada_retained"
  let script_input_ada  =  ada_in_inputs_with_policy(tx, policy_id)
  let script_output_ada = ada_in_outputs_with_policy(tx, policy_id)
  script_output_ada + tx.fee + allowance >= script_input_ada
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

pub fn collateral_sent_to_publisher(
  tx: Transaction,
  policy_id: PolicyId,
  new_channel: ChannelId,
) -> Bool {
  trace @"collateral_sent_to_publisher"
  let stt_name = full_stt_name(new_channel)
  let state = get_stt_state(tx.outputs, policy_id, stt_name)
  expect SubChannel(sub_state) = state
  has_collateral_utxo(tx.outputs, sub_state.publisher)
}

pub fn collateral_sent_to_publishers(
  tx: Transaction,
  own_ref: OutputReference,
  new_channels: List<ChannelId>,
) -> Bool {
  trace @"collateral_sent_to_publishers"
  let policy_id = get_policy_id(own_ref, tx.inputs)
  list.all(
    new_channels,
    fn(ch) { collateral_sent_to_publisher(tx, policy_id, ch) },
  )
}

/// True iff `outputs` contains a UTXO that is valid as a collateral UTXO
/// for the given publisher:
///   - addressed to the publisher's VKH,
///   - exactly `collateral_lovelace` lovelace,
///   - ADA-only (no other assets),
///   - no datum (collateral UTXOs must be datum-free),
///   - no reference script.
fn has_collateral_utxo(
  outputs: List<Output>,
  publisher: VerificationKeyHash,
) -> Bool {
  list.any(outputs, fn(o) { is_collateral_utxo(o, publisher) })
}

fn is_collateral_utxo(
  output: Output,
  publisher: VerificationKeyHash,
) -> Bool {
  and {
    output.address.payment_credential == VerificationKey(publisher),
    assets.lovelace_of(output.value) == collateral_lovelace,
    assets.without_lovelace(output.value) == assets.zero,
    output.datum == NoDatum,
    output.reference_script == None,
  }
}
