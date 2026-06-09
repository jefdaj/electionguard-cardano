use aiken/collection/list
use cardano/assets.{PolicyId}
use cardano/transaction.{
  Datum, InlineDatum, NoDatum, OutputReference, Transaction, find_input
}

use election/types/action.{
  ElectionAction,
  BurnTestTokens,
  InitElection, AddSubChannels, AdvancePhase, EndElection,
  RmSubChannels, RebalanceFunds, PostPublicRecords,
}
use election/cont.{
  init_election,
  add_subchannels, rm_subchannels, post_public_records,
  advance_phase, rebalance_funds_admin, rebalance_funds_subchannel,
}
use election/fund.{ada_retained_during_election}
use election/types/phase.{is_initial_phase, is_final_phase, is_valid_phase_transition}
use election/types/record.{validate_records}
use election/types/channel_id.{ChannelId}
use election/types/channel.{
  ChannelState, AdminChannel, AdminChannelState, SubChannel, SubChannelState,
  get_new_records,
}
use election/mint.{
  exact_channels_minted, exact_channels_burned,
  no_mints_for_policy,
  tx_burns_all, tx_only_burns,
}
use election/auth.{
  admin_authorized_spend, admin_signed, publisher_signed,
}
use election/stt.{
  get_initial_state, get_continuation_state,
  channels_kept_separate,
  correct_n_channels_updated,
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
  trace @"validate_admin_channel_mint"
  let channel_id = "admin"
  when redeemer is {
    InitElection -> {
      trace @"initelection branch"
      // No need to check for authorization here because whoever mints a
      // new admin STT will become the admin of their new election.
      expect Some(_) = tx.inputs |> find_input(oneshot_ref)
      let mints_admin_stt_only = exact_channels_minted(tx, policy_id, [channel_id]) ?

      // Special case: we validate the cont state here rather than in spend(),
      // because for InitElection there is no spend:
      let init_state: AdminChannelState = get_initial_state(tx)
      let expected: AdminChannelState = init_election(init_state.admin)
      let cont_as_expected = (init_state == expected) ?

      mints_admin_stt_only && cont_as_expected
    }
    EndElection -> {
      // No need to check for authorization here because the ledger will
      // require that the admin STT is one of the inputs, and the spend
      // validator will require that the admin signed in order to spend it.
      let burns_admin_stt_only = exact_channels_burned(tx, policy_id, [channel_id]) ?
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
  trace @"validate_subchannel_mints"
  let admin_auth = admin_authorized_spend(tx, policy_id) ?
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
  trace @"validate_mint"
  when redeemer is {
    BurnTestTokens -> tx_only_burns(policy_id, tx)
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

// TODO should this be part of the mint validator?
// fn validate_initelection_spend(
//   redeemer: ElectionAction,
//   tx: Transaction,
// ) -> Bool {
//   trace @"validate_initelection_spend"
// 
//   // TODO is there a cleaner way?
//   expect InitElection = redeemer
// 
//   // Special case because there's no input STT to get it the regular way.
//   let init_state: AdminChannelState = get_initial_state(tx)
// 
//   // TODO does this obsolete the other checks below?
//   let expected: AdminChannelState = init_election(init_state.admin)
//   let cont_as_expected = (init_state == expected) ?
// 
//   let new_records_empty = (list.length(init_state.new_records) == 0) ?
//   let subchannels_empty = (list.length(init_state.subchannels) == 0) ?
//   let seq_zero = (init_state.seq == 0) ?
//   let initial_phase = is_initial_phase(init_state.phase) ?
//   and {
//     cont_as_expected,
//     new_records_empty,
//     subchannels_empty,
//     seq_zero,
//     initial_phase,
//   }
// }

// TODO any reason to check or restrict where the new channel STTs are sent?
fn validate_addsubchannels_spend(
  state: ChannelState,
  own_ref: OutputReference,
  tx: Transaction,
  new_channels: List<ChannelId>
) -> Bool {
  trace @"validate_addsubchannels_spend"

  expect AdminChannel(admin_state) = state

  // The new subchannel STTs aren't being spent, so this will only be called once with the admin STT.
  expect AdminChannel(cont_state) = get_continuation_state(state, own_ref, tx)

  // TODO merge into one lib fn?
  let new_channels_valid  = are_disjoint(new_channels, ["admin"]) ? // TODO enforce [a-z]*[0-9]*?
  let new_channels_unique = are_disjoint(admin_state.subchannels, new_channels) ?

  let expected = add_subchannels(admin_state, new_channels, cont_state.phase)
  // trace @"expected" : expected
  // trace @"cont_state" : cont_state
  let cont_as_expected = (cont_state == expected) ?
  
  // The new phase could still be ConfigOnboardingPhase,
  // or it could advance to ConfigCeremonyPhase.
  let phase_valid = is_valid_phase_transition(admin_state.phase, cont_state.phase) ?

  let channels_separate = channels_kept_separate(own_ref, tx) ?

  and {
    new_channels_valid,
    new_channels_unique,
    cont_as_expected,
    phase_valid,
    channels_separate,
  }
}

fn validate_advancephase_spend(
  state: ChannelState,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"validate_advancephase_spend"
  expect AdminChannel(admin_state) = state
  expect AdminChannel(cont_state) = get_continuation_state(state, own_ref, tx)
  let valid_transition = is_valid_phase_transition(admin_state.phase, cont_state.phase) ?
  let expected = advance_phase(admin_state, cont_state.phase)
  // trace @"expected" : expected
  // trace @"cont_state" : cont_state
  let cont_as_expected = (cont_state == expected) ?
  valid_transition && cont_as_expected
}

fn validate_endelection_spend(
  state: ChannelState,
) -> Bool {
  trace @"validate_endelection_spend"
  // No need to check for lack of a continuation STT here; mint() handles that.
  expect AdminChannel(AdminChannelState { subchannels, phase, .. }) = state
  let final_phase = is_final_phase(phase) ?
  let subchannels_empty = (list.length(subchannels) == 0) ?
  final_phase && subchannels_empty
}

// Will be called once with Some(admin STT), or None for InitElection.
pub fn validate_admin_single_channel_spend(
  state: ChannelState,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"validate_admin_single_channel_spend"
  let authorized = admin_signed(own_ref, tx) ?
  authorized && when redeemer is {
    AddSubChannels { channels } -> validate_addsubchannels_spend(state, own_ref, tx, channels)
    AdvancePhase                -> validate_advancephase_spend(state, own_ref, tx)
    EndElection                 -> validate_endelection_spend(state)
    _                           -> False
  }
}

fn validate_rmsubchannels_admin_spend(
  admin_state: AdminChannelState,
  cont_state: ChannelState,
  own_ref: OutputReference,
  tx: Transaction,
  channels_to_rm: List<ChannelId>
) -> Bool {
  trace @"validate_rmsubchannels_admin_spend"
  expect AdminChannel(admin_cont_state) = cont_state

  // TODO allow at other times too?
  let final_phase = is_final_phase(admin_state.phase) ?

  let valid_transition = is_valid_phase_transition(admin_state.phase, admin_cont_state.phase) ?

  let expected = rm_subchannels(admin_state, channels_to_rm, admin_cont_state.phase)
  let cont_as_expected = (admin_cont_state == expected) ?

  // This check could go in the outer scope, but putting it here
  // prevents having to run it many times per TX.
  let n_channels_correct = correct_n_channels_updated(own_ref, tx, channels_to_rm)

  and {
    final_phase,
    valid_transition,
    cont_as_expected,
    n_channels_correct,
  }
}

fn validate_rmsubchannels_sub_spend(
  sub_state: SubChannelState,
  channels: List<ChannelId>,
) -> Bool {
  trace @"validate_rmsubchannels_sub_spend"
  // No need to check for lack of a continuation STT here; mint() handles that.

  // This checks that all the channels updated are in the declared channels list
  // (one channel checked per call). Combined with n_channels_correct in
  // validate_rmsubchannels_admin_spend above, it should ensure that the redeemer
  // channels list is correct.
  let valid_channel = list.has(channels, sub_state.channel_id) ?
  valid_channel
}

fn validate_rmsubchannels_spend(
  state: ChannelState,
  own_ref: OutputReference,
  tx: Transaction,
  channels: List<ChannelId>,
) -> Bool {
  trace @"validate_rmsubchannels_spend"
  when state is {
    AdminChannel(admin_state) -> {
      let cont_state = get_continuation_state(state, own_ref, tx)
      validate_rmsubchannels_admin_spend(admin_state, cont_state, own_ref, tx, channels)
    }
    SubChannel(sub_state) ->
      validate_rmsubchannels_sub_spend(sub_state, channels)
  }
}

fn validate_rebalancefunds_admin_spend(
  admin_state: AdminChannelState,
  cont_state: ChannelState,
  own_ref: OutputReference,
  tx: Transaction,
  channels: List<ChannelId>,
) -> Bool {
  trace @"validate_rebalancefunds_admin_spend"
  expect AdminChannel(admin_cont_state) = cont_state
  let valid_transition = is_valid_phase_transition(admin_state.phase, admin_cont_state.phase) ?
  let expected = rebalance_funds_admin(admin_state, admin_cont_state.phase)
  let cont_as_expected = (admin_cont_state == expected) ?

  // This check could go in validate_rebalancefunds_spend, but putting it here
  // prevents having to run it many times per TX. Combined with the
  // valid_channel check in validate_rebalancefunds_sub_spend below, this
  // should ensure that the redeemer channel list is correct.
  let n_channels_correct = correct_n_channels_updated(own_ref, tx, channels) ?

  and {
    valid_transition,
    n_channels_correct,
    cont_as_expected,
  }
}

fn validate_rebalancefunds_sub_spend(
  sub_state: SubChannelState,
  cont_state: ChannelState,
  channels: List<ChannelId>,
) -> Bool {
  trace @"validate_rebalancefunds_sub_spend"
  expect SubChannel(sub_cont_state) = cont_state

  // This checks that all the channels updated are in the declared channels list
  // (one channel checked per call). Combined with n_channels_correct in
  // validate_rebalancefunds_admin_spend above, it should ensure that the redeemer
  // channels list is correct.
  let valid_channel = list.has(channels, sub_state.channel_id) ?

  let expected = rebalance_funds_subchannel(sub_state) 
  let cont_as_expected = (sub_cont_state == expected) ?
  valid_channel && cont_as_expected
}

// ADA transfers are handled by the ledger, and we already checked that
// the overall script amount is retained, so this is almost a no-op: just
// increment seq. Phase can optionally also be advanced.
fn validate_rebalancefunds_spend(
  state: ChannelState,
  own_ref: OutputReference,
  tx: Transaction,
  channels: List<ChannelId>,
) -> Bool {
  trace @"validate_rebalancefunds_spend"
  let cont_state = get_continuation_state(state, own_ref, tx)
  when state is {
    AdminChannel(admin_state) ->
      validate_rebalancefunds_admin_spend(admin_state, cont_state, own_ref, tx, channels)
    SubChannel(sub_state) ->
      validate_rebalancefunds_sub_spend(sub_state, cont_state, channels)
   }
}

// Will be called once with admin STT + once with each subchannel STT.
pub fn validate_admin_multi_channel_spend(
  state: ChannelState,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"validate_admin_multi_channel_spend"
  let authorized = admin_signed(own_ref, tx) ?
  let separate = channels_kept_separate(own_ref, tx) ?
  authorized && separate && when redeemer is {
    RmSubChannels  { channels } -> validate_rmsubchannels_spend(state, own_ref, tx, channels)
    RebalanceFunds { channels } -> validate_rebalancefunds_spend(state, own_ref, tx, channels)
    _ -> False
  }
}

// Will be called once with either the admin or a subchannel STT.
pub fn validate_anyone_single_channel_spend(
  state: ChannelState,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"validate_anyone_single_channel_spend"

  // Gotcha: admin_signed wouldn't do here, because we don't want the admin to
  // be able to post to a non-admin channel.
  let authorized = publisher_signed(state, tx) ?

  // The only "anyone, single channel" redeemer so far
  expect PostPublicRecords = redeemer

  let cont_state = get_continuation_state(state, own_ref, tx)
  let new_records = get_new_records(state, cont_state)

  // The new records (or at least their CIDs + metadata) must be valid
  let new_records_valid = validate_records(new_records) ?

  // Optional phase transition when posting to admin channel
  let (opt_cont_phase, phase_valid) = when state is {
    AdminChannel(admin_state) -> {
      expect AdminChannel(AdminChannelState { phase, .. }) = cont_state
      (Some(phase), is_valid_phase_transition(admin_state.phase, phase))
    }
    SubChannel(_) -> (None, True) // subchannels have no phase (yet)
  }

  // And the continuation (next) state must be exactly as expected:
  // new_records replaced, seq incremented, the rest unchanged
  let expected = post_public_records(state, new_records, opt_cont_phase)
  let cont_as_expected = (cont_state == expected) ?

  and {
    authorized,
    new_records_valid,
    phase_valid,
    cont_as_expected,
  }
}

pub fn validate_spend(
  state: ChannelState,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"validate_spend"
  let ada_retained = ada_retained_during_election(redeemer, own_ref, tx) ?
  ada_retained && when redeemer is {
    BurnTestTokens -> tx_burns_all(own_ref, tx)
    InitElection -> False // init should never need to spend a contract output
    AddSubChannels { .. } | AdvancePhase | EndElection ->
      validate_admin_single_channel_spend(state, redeemer, own_ref, tx)
    RmSubChannels { .. } | RebalanceFunds { .. } ->
      validate_admin_multi_channel_spend(state, redeemer, own_ref, tx)
    PostPublicRecords ->
      validate_anyone_single_channel_spend(state, redeemer, own_ref, tx)
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
    trace @"mint"
    validate_mint(oneshot_ref, redeemer, policy_id, tx)
  }
  // TODO ah I get it: spend isn't called in the initial tx, so it can always expect a datum
  spend(
    datum: Option<ChannelState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    tx: Transaction,
  ) {
    trace @"spend"
    expect Some(state) = datum
    validate_spend(state, redeemer, own_ref, tx)
    // when datum is {
      // NoDatum -> validate_initelection_spend(redeemer, tx)
      // InlineDatum(d) -> {
        // expect state: ChannelState = d
      // }
      // _ -> False
    // }
  }
}
