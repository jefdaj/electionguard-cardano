use aiken/collection/list
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId, has_any_nft}
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
  tx_mints, tx_mints_all, tx_sends_token_to_addr,
}

use election/utils.{
  are_disjoint, tx_signed_by
}

// ===========================================
// Mint validator
// ===========================================

// Confirm that none of our tokens are being minted or burned.
pub fn no_mints_for_policy(policy_id: PolicyId, tx: Transaction) -> Bool {
  ! has_any_nft(tx.mint, policy_id)
}

pub fn validate_mint(
  oneshot_ref: OutputReference,
  action: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction,
) -> Bool {
  when action is {

    // Admin STT
    InitElection -> todo @"init election mint"
    EndElection  -> todo @"end election mint"

    // Subchannel STTs
    AddSubChannels { .. } -> todo "add subchannels mint"
    RmSubChannels  { .. } -> todo "rm subchannels mint"

    // No mints
    AdvancePhase          -> no_mints_for_policy(policy_id, tx)
    PostPublicRecords     -> no_mints_for_policy(policy_id, tx)
    RebalanceFunds { .. } -> no_mints_for_policy(policy_id, tx)

  }
}

// ===========================================
// Spend validator
// ===========================================

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
    todo @"spend"
  }
}
