use aiken/collection/list
use cardano/assets.{PolicyId}
use cardano/transaction.{
  OutputReference, Transaction, find_input
}

use election/action.{
  ElectionAction, InitElection, AddSubChannels, AdvancePhase, EndElection,
  RmSubChannels, RebalanceFunds, PostPublicRecords,
}
use election/funding.{ada_retained_during_election}
use election/phase.{is_initial_phase, is_final_phase, is_valid_phase_transition}
use election/record.{validate_records}
use election/state.{
  ChannelId, ChannelState,
  AdminChannel, AdminChannelState,
  add_subchannels, post_public_records, get_new_records,
}
// rm_subchannels, add_subchannels,
use election/stt.{
  exact_channels_minted,
  exact_channels_burned, no_mints_for_policy, full_stt_name,
  admin_authorized_tx, get_continuation_state,
  admin_signed, publisher_signed,
}

use election/utils.{are_disjoint}

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
      // new admin STT will become the admin of their new election.
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

// These also check that the admin STT isn't being changed.
// TODO make that more obvious
pub fn validate_subchannel_mints(
  redeemer: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  // TODO unify with admin_signed?
  let admin_auth = admin_authorized_tx(tx, policy_id) ?
  admin_auth && when redeemer is {
    AddSubChannels { channels } -> {
      let mints_as_expected = exact_channels_minted(tx, policy_id, channels) ?
      mints_as_expected
    }
    RmSubChannels { channels } -> {
      let mints_as_expected = exact_channels_burned(tx, policy_id, channels) ?
      mints_as_expected
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

fn validate_initelection_spend(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {

  // This is currently true, but remember to remove it if we run into a
  // use case for opening a channel starting from another script.
  expect None = datum

  // Has a special to find the new admin state when datum is None.
  expect AdminChannel(cont_state) = get_continuation_state(None, own_ref, tx)

  let new_records_empty = (list.length(cont_state.new_records) == 0) ?
  let subchannels_empty = (list.length(cont_state.subchannels) == 0) ?
  let seq_zero = (cont_state.seq == 0) ?
  let initial_phase = is_initial_phase(cont_state.phase) ?
  and {
    new_records_empty,
    subchannels_empty,
    seq_zero,
    initial_phase,
  }
}

// TODO any reason to check or restrict where the new channel STTs are sent?
fn validate_addsubchannels_spend(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
  new_channels: List<ChannelId>
) -> Bool {

  // The new subchannel STTs aren't being spent, so this will only be called once with the admin STT.
  expect Some(AdminChannel(state)) = datum
  expect AdminChannel(cont_state) = get_continuation_state(datum, own_ref, tx)

  // TODO merge into one lib fn?
  let new_channels_valid  = are_disjoint(new_channels, ["admin"]) ? // TODO enforce [a-z]*[0-9]*?
  let new_channels_unique = are_disjoint(state.subchannels, new_channels) ?

  let expected = add_subchannels(state, new_channels, cont_state.phase)
  let cont_as_expected = (cont_state == expected) ?
  
  // The new phase could still be ConfigOnboardingPhase,
  // or it could advance to ConfigCeremonyPhase.
  let phase_valid = is_valid_phase_transition(state.phase, cont_state.phase) ?

  and {
    new_channels_valid,
    new_channels_unique,
    cont_as_expected,
    phase_valid,
  }
}

fn validate_advancephase_spend(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  expect Some(AdminChannel(state)) = datum
  expect AdminChannel(cont_state) = get_continuation_state(datum, own_ref, tx)
  let valid_transition = is_valid_phase_transition(state.phase, cont_state.phase) ?
  let expected = AdminChannelState {..state, phase: cont_state.phase}
  let cont_as_expected = (cont_state == expected) ?
  valid_transition && cont_as_expected
}

// No need to check for lack of a continuation STT here,
// because the mint validator handles that.
fn validate_endelection_spend(
  datum: Option<ChannelState>,
) -> Bool {
  expect Some(AdminChannel(AdminChannelState { subchannels, phase, .. })) = datum
  let final_phase = is_final_phase(phase) ?
  let subchannels_empty = (list.length(subchannels) == 0) ?
  final_phase && subchannels_empty
}

// Will be called once with Some(admin STT), or None for InitElection.
pub fn validate_admin_single_channel_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  let authorized = admin_signed(own_ref, tx) ?
  authorized && when redeemer is {
    InitElection                -> validate_initelection_spend(datum, own_ref, tx)
    AddSubChannels { channels } -> validate_addsubchannels_spend(datum, own_ref, tx, channels)
    AdvancePhase                -> validate_advancephase_spend(datum, own_ref, tx)
    EndElection                 -> validate_endelection_spend(datum)
    _                           -> False
  }
}

// Will be called once with admin STT + once with each subchannel STT.
pub fn validate_admin_multi_channel_spend(
  _datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  let authorized = admin_signed(own_ref, tx) ?
  authorized && when redeemer is {
    RmSubChannels  { .. } -> todo @"rm subchannels spend"
    RebalanceFunds { .. } -> todo @"rebalance funds spend"
    _ -> False
  }
}

// Will be called once with either the admin or a subchannel STT.
pub fn validate_anyone_single_channel_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {

  // Gotcha: admin_signed wouldn't do here, because we don't want the admin to
  // be able to post to a non-admin channel.
  let authorized = publisher_signed(datum, own_ref, tx) ?

  // The only "anyone, single channel" redeemer so far
  expect PostPublicRecords = redeemer

  expect Some(state) = datum
  let cont_state = get_continuation_state(datum, own_ref, tx)
  let new_records = get_new_records(state, cont_state)

  // The new records (or at least their CIDs + metadata) must be valid
  let new_records_valid = validate_records(new_records) ?

  // And the continuation (next) state must be exactly as expected:
  // new_records replaced, seq incremented, the rest unchanged
  let expected = post_public_records(state, new_records)
  let cont_as_expected = (cont_state == expected) ?

  and {
    authorized,
    new_records_valid,
    cont_as_expected,
  }
}

pub fn validate_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  let ada_retained = ada_retained_during_election(redeemer, own_ref, tx) ?
  ada_retained && when redeemer is {
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
