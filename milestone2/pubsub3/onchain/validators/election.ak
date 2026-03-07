// use aiken/collection/list
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}

use election/action.{
  ElectionAction, InitElection, AddSubChannels, AdvancePhase, EndElection,
  RmSubChannels, RebalanceFunds, PostPublicRecords,
}
use election/funding.{
  channel_ada_preserved
}
use election/phase.{
  ElectionConfigPhase, ConfigOnboardingPhase, is_initial_phase, is_final_phase,
  is_valid_phase_transition,
}
use election/record.{
  validate_records
}
use election/state.{
  ChannelState, AdminChannel, AdminChannelState, SubChannel, SubChannelState,
  extract_admin_state, get_stt_name, get_admin_stt_name, add_subchannels,
  rm_subchannels, post_public_records,
}
use election/stt.{
  tx_mints, tx_mints_all, tx_sends_token_to_addr, no_mints_for_policy
}

use election/utils.{
  are_disjoint, tx_signed_by
}

// ===========================================
// Mint validator
// ===========================================

pub fn validate_admin_channel_mint(
  oneshot_ref: OutputReference,
  action: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  when action is {
    InitElection -> todo @"init election mint"
    EndElection  -> todo @"end election mint"
    _ -> False
  }
}

pub fn validate_subchannel_mint(
  action: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  when action is {
    AddSubChannels { .. } -> todo @"add subchannels mint"
    RmSubChannels  { .. } -> todo @"rm subchannels mint"
    _ -> False
  }
}

pub fn validate_mint(
  oneshot_ref: OutputReference,
  action: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  when action is {
    InitElection | EndElection ->
      validate_admin_channel_mint(oneshot_ref, action, policy_id, tx)
    AddSubChannels { .. } | RmSubChannels { .. } ->
      validate_subchannel_mint(action, policy_id, tx)
    AdvancePhase | PostPublicRecords | RebalanceFunds { .. } ->
      no_mints_for_policy(policy_id, tx)
  }
}

// ===========================================
// Spend validator
// ===========================================

pub fn validate_admin_single_channel_spend(
  state: Option<ChannelState>,
  action: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  when action is {
    InitElection          -> todo @"init election spend"
    AddSubChannels { .. } -> todo @"add subchannels spend"
    AdvancePhase          -> todo @"advance phase spend"
    EndElection           -> todo @"end election spend"
    _ -> False
  }
}

pub fn validate_admin_multi_channel_spend(
  state: Option<ChannelState>,
  action: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  when action is {
    RmSubChannels  { .. } -> todo @"rm subchannels spend"
    RebalanceFunds { .. } -> todo @"rebalance funds spend"
    _ -> False
  }
}

pub fn validate_anyone_single_channel_spend(
  state: Option<ChannelState>,
  action: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  when action is {
    PostPublicRecords -> todo "post public records spend"
    _ -> False
  }
}

pub fn validate_spend(
  state: Option<ChannelState>,
  action: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) {
  when action is {
    InitElection | AddSubChannels { .. } | AdvancePhase | EndElection ->
      validate_admin_single_channel_spend(state, action, own_ref, tx)
    RmSubChannels { .. } | RebalanceFunds { .. } ->
      validate_admin_multi_channel_spend(state, action, own_ref, tx)
    PostPublicRecords ->
      validate_anyone_single_channel_spend(state, action, own_ref, tx)
  }
}

// ===========================================
// Main validator
// ===========================================

validator election(oneshot_ref: OutputReference) {
  mint(
    action: ElectionAction,
    policy_id: PolicyId,
    tx: Transaction
  ) {
    validate_mint(oneshot_ref, action, policy_id, tx)
  }
  spend(
    state: Option<ChannelState>,
    action: ElectionAction,
    own_ref: OutputReference,
    tx: Transaction,
  ) {
    validate_spend(state, action, own_ref, tx)
  }
}
