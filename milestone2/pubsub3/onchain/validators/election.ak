use aiken/collection/list
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}

use election/action.{
  ElectionAction, InitElection, AddSubChannels, AdvancePhase, EndElection,
  RmSubChannels, RebalanceFunds, PostPublicRecords,
}
// use election/funding.{
//   channel_ada_preserved
// }
// use election/phase.{
//   ElectionConfigPhase, ConfigOnboardingPhase, is_initial_phase, is_final_phase,
//   is_valid_phase_transition,
// }
use election/record.{
  PublicRecord,
  validate_records
}
use election/state.{
  ChannelState, AdminChannel, AdminChannelState, SubChannel, SubChannelState,
  post_public_records,
  get_stt_name,
}
// rm_subchannels, add_subchannels,
use election/stt.{
  exact_channels_minted,
  exact_channels_burned, no_mints_for_policy, full_stt_name,
  admin_authorized_tx
}

// use election/utils.{
//   are_disjoint, tx_signed_by
// }

// ===========================================
// Mint validator
// ===========================================

pub fn validate_admin_channel_mint(
  oneshot_ref: OutputReference,
  redeemer: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  let stt_name = full_stt_name("admin")
  when redeemer is {
    InitElection -> {
      // No need to check for authorization here because whoever mints a
      // new admin STT will become the admin of that election.
      expect Some(_) = tx.inputs |> find_input(oneshot_ref)
      let mints_admin_stt_only = exact_channels_minted(tx, policy_id, [stt_name]) ?
      mints_admin_stt_only
    }
    EndElection -> {
      // No need to check for authorization here because the ledger will
      // require that the admin STT is one of the inputs, and the spend
      // validator will require that the admin signed in order to spend it.
      let burns_admin_stt_only = exact_channels_burned(tx, policy_id, [stt_name]) ?
      burns_admin_stt_only
    }
    _ -> False
  }
}

pub fn validate_subchannel_mints(
  redeemer: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  let admin_auth = admin_authorized_tx(tx, policy_id) ?
  when redeemer is {
    AddSubChannels { channels } -> {
      let mints_burns_as_expected = exact_channels_minted(tx, policy_id, channels) ?
      admin_auth && mints_burns_as_expected
    }
    RmSubChannels { channels } -> {
      let mints_burns_as_expected = exact_channels_burned(tx, policy_id, channels) ?
      admin_auth && mints_burns_as_expected
    }
    _ -> False
  }
}

// Remember this will be called once per policy_id, not per token minted.
// So it should validate all the election STTs in one go.
pub fn validate_mint(
  oneshot_ref: OutputReference,
  redeemer: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  when redeemer is {
    InitElection | EndElection ->
      validate_admin_channel_mint(oneshot_ref, redeemer, policy_id, tx)
    AddSubChannels { .. } | RmSubChannels { .. } ->
      validate_subchannel_mints(redeemer, policy_id, tx)
    AdvancePhase | PostPublicRecords | RebalanceFunds { .. } ->
      no_mints_for_policy(policy_id, tx)
  }
}

// ===========================================
// Spend validator
// ===========================================

// Will be called once with Some(admin STT), or None for InitElection.
pub fn validate_admin_single_channel_spend(
  _datum: Option<ChannelState>,
  redeemer: ElectionAction,
  _own_ref: OutputReference,
  _tx: Transaction,
) {
  when redeemer is {
    InitElection          -> todo @"init election spend"
    AddSubChannels { .. } -> todo @"add subchannels spend"
    AdvancePhase          -> todo @"advance phase spend"
    EndElection           -> todo @"end election spend"
    _ -> False
  }
}

// Will be called once with admin STT + once with each subchannel STT.
pub fn validate_admin_multi_channel_spend(
  _datum: Option<ChannelState>,
  redeemer: ElectionAction,
  _own_ref: OutputReference,
  _tx: Transaction,
) {
  when redeemer is {
    RmSubChannels  { .. } -> todo @"rm subchannels spend"
    RebalanceFunds { .. } -> todo @"rebalance funds spend"
    _ -> False
  }
}

fn find_new_state(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> Option<ChannelState> {
  // Get own input to extract script address and policy
  expect Some(own_input) = tx.inputs |> list.find(fn(i) { i.output_reference == own_ref })
  expect Script(policy_id) = own_input.output.address.payment_credential
  
  let script_addr = own_input.output.address
  let stt_name = get_stt_name(datum)

  // Find the output containing the STT in one step
  let opt_stt =
    list.find(tx.outputs, fn(output) {
      output.address == script_addr && 
      assets.quantity_of(output.value, policy_id, stt_name) == 1
    })

  when opt_stt is {
    None -> None
    Some(stt_output) -> {
      expect InlineDatum(new_datum) = stt_output.datum
      expect new_state: ChannelState = new_datum
      Some(new_state)
    }
  }
}

fn get_new_records(
  old_state: ChannelState,
  new_state: ChannelState,
) -> List<PublicRecord> {
  // Old and new types must match: both AdminChannel or both SubChannel
  when old_state is {
    AdminChannel(_) -> {
      expect AdminChannel(new_admin_state) = new_state
      new_admin_state.new_records
    }   
    SubChannel(_) -> {
      expect SubChannel(new_admin_state) = new_state
      new_admin_state.new_records
    }   
  }
}

// Will be called once with either the admin or a subchannel STT.
// TODO which parts of this should be factored out into helper functions?
pub fn validate_anyone_single_channel_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {

  // The only "anyone, single channel" redeemer so far
  expect PostPublicRecords = redeemer

  expect Some(old_state) = datum
  expect Some(new_state) = find_new_state(datum, own_ref, tx)

  let new_records = get_new_records(old_state, new_state)

  // The new records (or at least their CIDs + metadata) must be valid
  let records_valid = validate_records(new_records) ?

  // And the next state must be exactly as expected: new_records replaced, seq incremented
  let new_expected = post_public_records(old_state, new_records)
  let new_state_as_expected = (new_expected == new_state) ?

  and {
    records_valid,
    new_state_as_expected,
  }
}

pub fn validate_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  when redeemer is {
    InitElection | AddSubChannels { .. } | AdvancePhase | EndElection ->
      validate_admin_single_channel_spend(datum, redeemer, own_ref, tx)
    RmSubChannels { .. } | RebalanceFunds { .. } ->
      validate_admin_multi_channel_spend(datum, redeemer, own_ref, tx)
    PostPublicRecords ->
      validate_anyone_single_channel_spend(datum, redeemer, own_ref, tx)
  }
}

// ===========================================
// Main validator
// ===========================================

validator election(oneshot_ref: OutputReference) {
  mint(
    redeemer: ElectionAction,
    policy_id: PolicyId,
    tx: Transaction
  ) {
    validate_mint(oneshot_ref, redeemer, policy_id, tx)
  }
  spend(
    datum: Option<ChannelState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    tx: Transaction,
  ) {
    validate_spend(datum, redeemer, own_ref, tx)
  }
}
