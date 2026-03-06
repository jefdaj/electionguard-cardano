use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId, has_any_nft}

use election/action.{
  ElectionAction, AdminAct, RegularAct,
  AdminAction, InitElection,
  AddSubChannels, RmSubChannels,
  AdvancePhaseOnly, RebalanceFunds, EndElection,
  RegularAction, PostPublicRecords,
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
use election/utils.{
  tx_mints, tx_mints_all,
  tx_signed_by,
  tx_sends_token_to_addr,
  are_disjoint,
}

pub fn validate_admin_mint(
  action: AdminAction, // regular actions don't mint or burn
  policy_id: PolicyId,
  self: Transaction,
  oneshot_ref: OutputReference
) -> Bool {
  let stt_name = get_admin_stt_name()
  when action is {

    InitElection -> {
      expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
      let mints_admin_stt = tx_mints(self, policy_id, stt_name, 1) ?
      mints_admin_stt
    }

    AddSubChannels { channels } -> {
      let admin_stt_unchanged = tx_mints(self, policy_id, stt_name, 0) ?
      let mints_channel_stts = tx_mints_all(self, policy_id, channels, 1) ?
      and {
        admin_stt_unchanged,
        mints_channel_stts,
      }
    }

    RmSubChannels { channels } -> {
      let admin_stt_unchanged = tx_mints(self, policy_id, stt_name, 0) ?
      let burns_channel_stts = tx_mints_all(self, policy_id, channels, -1) ?
      and {
        admin_stt_unchanged,
        burns_channel_stts,
      }
    }

    AdvancePhaseOnly -> todo @"advance phase mint"

    RebalanceFunds -> assert_no_mints(policy_id, self)

    EndElection -> {
      let burns_admin_stt = tx_mints(self, policy_id, stt_name, -1) ?
      burns_admin_stt
    }

  }
}

// Confirm that none of our tokens are being minted or burned in a TX.
pub fn assert_no_mints(policy_id: PolicyId, tx: Transaction) -> Bool {
  ! has_any_nft(tx.mint, policy_id)
}

// This is defined by the redeemer; the datum can be a regular or admin state.
// (But the datum can't be None)
pub fn validate_regular_spend(
  old_state: ChannelState,
  new_state: ChannelState,
  action: RegularAction,
  self: Transaction,
) -> Bool {

  // regular actions must always preserve the STT
  // expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
  // expect InlineDatum(new_state) = stt_output.datum

  // TODO back to a when clause once there's more than one regular action
  // TODO should new_records be passed as part of the redeemer here too?
  let PostPublicRecords = action

  let old_vkh = when old_state is {
    AdminChannel(AdminChannelState { admin, .. }) -> admin
    SubChannel(SubChannelState { publisher, .. }) -> publisher
  }

  let new_records = when old_state is {
    AdminChannel(_) -> {
      expect AdminChannel(new_admin_state) = new_state
      new_admin_state.new_records
    }
    SubChannel(_) -> {
      expect SubChannel(new_sub_state) = new_state
      new_sub_state.new_records
    }
  }

  let vkh_signed = tx_signed_by(self, old_vkh) ?
  let new_records_valid = validate_records(new_records) ?
  let expected_new_state = post_public_records(old_state, new_records)
  let new_state_as_expected = (expected_new_state == new_state) ?

  and {
    vkh_signed,
    new_records_valid,
    new_state_as_expected,
    // todo @"channel funds above minimum", // TODO and define a reasonable minimum
    // todo @"channel funds stay with STT",
  }

}

// This is defined by the redeemer; the datum may be none or an admin state.
pub fn validate_admin_spend(
  old_state: Option<AdminChannelState>,
  new_state: Option<AdminChannelState>,
  action: AdminAction,
  self: Transaction,
) -> Bool {
  when action is {
    InitElection -> {

      // This is currently true, but remember to remove it if we run into a
      // use case for opening a channel starting from another script.
      // TODO remove anyway, since it's not technically required?
      expect None = old_state

      expect Some(new_admin_state) = new_state

      // expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
      // expect InlineDatum(new_state) = stt_output.datum
      // expect new_state: AdminChannelState = new_state
      let vkh_signed = tx_signed_by(self, new_admin_state.admin) ?
      let new_records_empty = (list.length(new_admin_state.new_records) == 0) ?
      let subchannels_empty = (list.length(new_admin_state.subchannels) == 0) ?
      let seq_zero = (new_admin_state.seq == 0) ?
      let initial_phase = is_initial_phase(new_admin_state.phase) ?
      and {
        vkh_signed,
        new_records_empty,
        subchannels_empty,
        seq_zero,
	initial_phase,
	// todo @"admin channel funds above minimum" // TODO and define a reasonable minimum
      }
    }

    // TODO any reason to check or restrict where the new channel STTs are sent?
    AddSubChannels { channels } -> {
      expect Some(old_admin_state) = old_state
      expect Some(new_admin_state) = new_state
      let vkh_signed = tx_signed_by(self, new_admin_state.admin) ?
      let new_channels_valid  = are_disjoint(channels, ["admin"]) ? // TODO enforce [a-z]*[0-9]*?
      let new_channels_unique = are_disjoint(old_admin_state.subchannels, channels) ?
      let expected_new_admin_state = add_subchannels(old_admin_state, channels)
      let new_state_as_expected = (new_admin_state == expected_new_admin_state) ?
      let valid_old_phase = (old_admin_state.phase == ElectionConfigPhase(ConfigOnboardingPhase)) ?

      // The new phase could still be ConfigOnboardingPhase, or it could advance to ConfigCeremonyPhase
      let valid_transition = is_valid_phase_transition(old_admin_state.phase, new_admin_state.phase) ?

      and {
        vkh_signed,
        new_channels_valid,
        new_channels_unique,
        new_state_as_expected,
	valid_old_phase,
	valid_transition,
	// todo @"all channel funds above minimum" // TODO and define a reasonable minimum
        // todo @"channel funds stay with STT",
      }
    }

    RmSubChannels { channels } -> {
      expect Some(old_admin_state) = old_state
      expect Some(new_admin_state) = new_state
      let vkh_signed = tx_signed_by(self, new_admin_state.admin) ?

      // This seems like it should work, but only because this is a special case of being in the final phase?
      // (Otherwise, would need to adjust phase in expected new state)
      let expected_new_admin_state = rm_subchannels(old_admin_state, channels)
      let new_state_as_expected = (new_admin_state == expected_new_admin_state) ?

      let valid_transition = is_valid_phase_transition(old_admin_state.phase, new_admin_state.phase) ?
      let final_phase = is_final_phase(old_admin_state.phase) ? // TODO allow at other times too?

      and {
        vkh_signed,
        new_state_as_expected,
	valid_transition,
	final_phase,
	// todo @"channel funds go to admin stt output"
      }
    }

    AdvancePhaseOnly -> todo @"advance phase spend"

    // TODO should the admin be able to also rebalance as part of other operations?
    RebalanceFunds -> todo @"rebalance channel funds"

    EndElection -> {
      expect Some(AdminChannelState { admin, subchannels, phase, .. }) = old_state
      expect None = new_state
      let vkh_signed = tx_signed_by(self, admin) ?
      let subchannels_empty = (list.length(subchannels) == 0) ?
      let final_phase = is_final_phase(phase) ?
      and {
        vkh_signed,
        subchannels_empty,
	final_phase,
	// todo @"dummy logic for deciding what admin can do with channel funds?"
      }
      // TODO require ADA goes back to admin or main channel
    }
  }
}

validator election(oneshot_ref: OutputReference) {

  mint(
    redeemer: ElectionAction,
    policy_id: PolicyId,
    self: Transaction
  ) {
    when redeemer is {
      AdminAct(action) -> validate_admin_mint(action, policy_id, self, oneshot_ref)
      RegularAct(_) -> assert_no_mints(policy_id, self)
    }
  }

  spend(
    old_datum: Option<ChannelState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {

    let stt_name = get_stt_name(old_datum)
    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address

    // During the election, we want to make sure that no one takes ADA out of
    // the channel fee pools, but also allow change from top-up transactions.
    // At the end of the election, the admin can send remaining ADA wherever
    // they want. In future versions, this would be a good place to add
    // treasury logic.
    let ada_retained_during_election = when redeemer is {
      AdminAct(EndElection) -> True
      _ -> channel_ada_preserved(self, policy_id)
    }

    when redeemer is {

      AdminAct(admin_act) -> {
        // for admin action:
        // - may be missing the old or new channel state
        // - can't be missing both, but we don't check that here
        // - channel state(s) must be admin channel states
	// TODO should the STT be tested in validate_admin_spend rather than here?
        let old_admin_state: Option<AdminChannelState> = extract_admin_state(old_datum)
        let new_admin_state: Option<AdminChannelState> =
          when tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1) is {
            None -> None
            Some(stt_output) -> {
              expect InlineDatum(new_datum) = stt_output.datum
              expect AdminChannel(new_admin_state) = new_datum
              Some(new_admin_state)
            }
          }
        ada_retained_during_election && 
	validate_admin_spend(old_admin_state, new_admin_state, admin_act, self)
      }

      RegularAct(reg_act) -> {
        // for regular action:
        // - must have old + new channel state
        // - the old + new states may be either for a regular or admin channel
        // - the state types must match, but we don't check that here
	// TODO should the STT be tested in validate_regular_spend rather than here?
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
        expect InlineDatum(new_datum) = stt_output.datum
        expect Some(old_state): Option<ChannelState> = old_datum
        expect Some(new_state): Option<ChannelState> = new_datum
        ada_retained_during_election && 
        validate_regular_spend(old_state, new_state, reg_act, self)
      }

    }

  }
}
