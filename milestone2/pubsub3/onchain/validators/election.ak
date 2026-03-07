use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId, has_any_nft}

use election/action.{
  ElectionAction,
  InitElection, AddSubChannels, AdvancePhase, EndElection,
  RmSubChannels, RebalanceFunds,
  PostPublicRecords,
}
use election/funding.{channel_ada_preserved}
use election/record.{validate_records}
use election/state.{
  ChannelState,
  AdminChannel, AdminChannelState,
  SubChannel, SubChannelState,
  extract_admin_state, get_stt_name, get_admin_stt_name,
  add_subchannels, rm_subchannels, post_public_records,
}
use election/phase.{
  ElectionConfigPhase, ConfigOnboardingPhase,
  is_initial_phase, is_final_phase,
  is_valid_phase_transition,
}
use election/stt.{
  tx_mints, tx_mints_all,
  tx_sends_token_to_addr,
}
use election/utils.{are_disjoint, tx_signed_by}

validator election(oneshot_ref: OutputReference) {

  mint(
    redeemer: ElectionAction,
    policy_id: PolicyId,
    self: Transaction
  ) {
    todo @"mint"
  }

  spend(
    old_datum: Option<ChannelState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {
    todo @"spend"
  }
}
