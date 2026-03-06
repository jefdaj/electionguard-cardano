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
  action: AdminAction,
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

    RebalanceFunds -> no_mints_for_policy(policy_id, self)

    AdvancePhaseOnly -> no_mints_for_policy(policy_id, self)

    EndElection -> {
      let burns_admin_stt = tx_mints(self, policy_id, stt_name, -1) ?
      burns_admin_stt
    }

  }
}

// Confirm that none of our tokens are being minted or burned in a TX.
pub fn no_mints_for_policy(policy_id: PolicyId, tx: Transaction) -> Bool {
  ! has_any_nft(tx.mint, policy_id)
}

// In a regular spend both old_state and new_state always exist.
// Their types must also match: both AdminChannelState or both SubChannelState.
pub fn validate_regular_spend(
  old: ChannelState,
  new: ChannelState,
  act: RegularAction,
) -> Bool {
  let PostPublicRecords = act
  let records = when old is {
    AdminChannel(_) -> {
      expect AdminChannel(new_admin) = new
      new_admin.new_records
    }
    SubChannel(_) -> {
      expect SubChannel(new_sub) = new
      new_sub.new_records
    }
  }
  let records_valid = validate_records(records) ?
  let expected = post_public_records(old, records)
  let state_valid = (expected == new) ?
  and {
    records_valid,
    state_valid,
  }
}

// This is defined by the redeemer; the datum may be none or an admin state.
pub fn validate_admin_spend(
  old_state: Option<AdminChannelState>,
  new_state: Option<AdminChannelState>,
  action: AdminAction,
) -> Bool {
  when action is {

    InitElection -> {

      // This is currently true, but remember to remove it if we run into a
      // use case for opening a channel starting from another script.
      // TODO remove anyway, since it's not technically required?
      expect None = old_state

      expect Some(new_admin_state) = new_state

      let new_records_empty = (list.length(new_admin_state.new_records) == 0) ?
      let subchannels_empty = (list.length(new_admin_state.subchannels) == 0) ?
      let seq_zero = (new_admin_state.seq == 0) ?
      let initial_phase = is_initial_phase(new_admin_state.phase) ?
      and {
        new_records_empty,
        subchannels_empty,
        seq_zero,
	initial_phase,
      }
    }

    // TODO any reason to check or restrict where the new channel STTs are sent?
    AddSubChannels { channels } -> {
      expect Some(old_admin_state) = old_state
      expect Some(new_admin_state) = new_state
      let new_channels_valid  = are_disjoint(channels, ["admin"]) ? // TODO enforce [a-z]*[0-9]*?
      let new_channels_unique = are_disjoint(old_admin_state.subchannels, channels) ?
      let expected_new_admin_state = add_subchannels(old_admin_state, channels)
      let new_state_as_expected = (new_admin_state == expected_new_admin_state) ?
      let valid_old_phase = (old_admin_state.phase == ElectionConfigPhase(ConfigOnboardingPhase)) ?

      // The new phase could still be ConfigOnboardingPhase, or it could advance to ConfigCeremonyPhase
      let valid_transition = is_valid_phase_transition(old_admin_state.phase, new_admin_state.phase) ?

      and {
        new_channels_valid,
        new_channels_unique,
        new_state_as_expected,
	valid_old_phase,
	valid_transition,
	// TODO set a min amount of channel funds to start with? it would work to omit
      }

    }

    RmSubChannels { channels } -> {
      expect Some(old_admin_state) = old_state
      expect Some(new_admin_state) = new_state

      // This seems like it should work, but only because this is a special case of being in the final phase?
      // (Otherwise, would need to adjust phase in expected new state)
      let expected_new_admin_state = rm_subchannels(old_admin_state, channels)
      let new_state_as_expected = (new_admin_state == expected_new_admin_state) ?

      let valid_transition = is_valid_phase_transition(old_admin_state.phase, new_admin_state.phase) ?
      let final_phase = is_final_phase(old_admin_state.phase) ? // TODO allow at other times too?

      and {
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
      expect Some(AdminChannelState { subchannels, phase, .. }) = old_state
      expect None = new_state
      let subchannels_empty = (list.length(subchannels) == 0) ?
      let final_phase = is_final_phase(phase) ?
      and {
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
      RegularAct(_) -> no_mints_for_policy(policy_id, self)
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
        let old_admin_state: Option<AdminChannelState> = extract_admin_state(old_datum)
        let new_admin_state: Option<AdminChannelState> =
	  // TODO make this clearer
          when tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1) is {
            None -> None
            Some(stt_output) -> {
              expect InlineDatum(new_datum) = stt_output.datum
              expect AdminChannel(new_admin_state) = new_datum
              Some(new_admin_state) // TODO don't shadow var names
            }
          }

	// Can normally get vkh from old state, unless this is the first step
	let vkh = when old_admin_state is {
	  Some(old_state) -> old_state.admin
	  None -> {
	    expect Some(new_state) = new_admin_state
	    new_state.admin
	  }
	}
        let vkh_signed = tx_signed_by(self, vkh) ?

	and {
	  vkh_signed,
          ada_retained_during_election,
	  validate_admin_spend(old_admin_state, new_admin_state, admin_act),
	}

      }

      RegularAct(reg_act) -> {

        // for regular action:
        // - must have old + new channel state
        // - the old + new states may be either for a regular or admin channel
        // - the state types must match, but we don't check that here
	// TODO helper function to check for stt_output?
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
        expect InlineDatum(new_datum) = stt_output.datum
        expect Some(old_state): Option<ChannelState> = old_datum
        expect Some(new_state): Option<ChannelState> = new_datum

        // There's always an old state for regular actions,
	// but the key is in different fields depending on the channel type
        let vkh = when old_state is {
          AdminChannel(AdminChannelState { admin, .. }) -> admin
          SubChannel(SubChannelState { publisher, .. }) -> publisher
        }
        let vkh_signed = tx_signed_by(self, vkh) ?

        and {
	  vkh_signed,
          ada_retained_during_election,
          validate_regular_spend(old_state, new_state, reg_act),
	}
      }

    }

  }
}
