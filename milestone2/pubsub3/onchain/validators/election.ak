use aiken/primitive/bytearray
use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use config

use election/action.{
  ElectionAction, AdminAct, RegularAct,
  AdminAction, InitElection, AddSubChannels, RmSubChannels, EndElection,
  RegularAction, PostPublicRecords,
}
use election/record.{validate_records}
use election/state.{
  ChannelState,
  AdminChannel, AdminChannelState,
  SubChannel, SubChannelState,
  extract_admin_state, get_stt_name
}
use election/utils.{tx_mints, tx_signed_by, tx_sends_token_to_addr}

pub fn validate_admin_mint(
  action: AdminAction, // regular actions don't mint or burn
  policy_id: PolicyId,
  self: Transaction,
  oneshot_ref: OutputReference
) -> Bool {
  let stt_name = bytearray.concat(config.stt_prefix, "-admin-channel") // TODO clean up
  when action is {

    InitElection -> {
      expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
      let stt_minted = tx_mints(self, policy_id, stt_name, 1) ?
      stt_minted
    }

    AddSubChannels { .. } -> { todo @"add subchannels" }
    RmSubChannels  { .. } -> { todo  @"rm subchannels" }

    EndElection -> {
      let stt_burned = tx_mints(self, policy_id, stt_name, -1) ?
      stt_burned
    }

  }
}

// This is defined by the redeemer; the datum can be a regular or admin state.
// (But the datum can't be None)
pub fn validate_regular_spend(
  datum: ChannelState,
  redeemer: RegularAction,
  self: Transaction,
  policy_id: PolicyId,
  stt_name: ByteArray,
  script_addr: Address,
) -> Bool {

  // regular actions must always preserve the STT
  expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
  expect InlineDatum(new_datum) = stt_output.datum

  // TODO back to a when clause once there's more than one regular action
  let PostPublicRecords = redeemer

  let (old_vkh, old_seq) = when datum is {
    AdminChannel(AdminChannelState { admin, seq, .. }) -> (admin, seq)
    SubChannel(SubChannelState { publisher, seq, .. }) -> (publisher, seq)
  }

  let (new_vkh, new_seq, new_records) = when datum is {
    AdminChannel(_) -> {
      expect new_state: AdminChannelState = new_datum
      (new_state.admin, new_state.seq, new_state.new_records)
    }
    SubChannel(_) -> {
      expect new_state: SubChannelState = new_datum
      (new_state.publisher, new_state.seq, new_state.new_records)
    }
  }

  let vkh_signed = tx_signed_by(self, old_vkh) ?
  let vkh_unchanged = new_vkh == old_vkh
  let seq_incremented = (new_seq == old_seq + 1) ?
  let new_records_valid = validate_records(new_records) ?

  and {
    vkh_signed,
    vkh_unchanged,
    seq_incremented,
    new_records_valid
  }

}

// This is defined by the redeemer; the datum may be none or an admin state.
pub fn validate_admin_spend(
  datum: Option<AdminChannelState>,
  redeemer: AdminAction,
  self: Transaction,
  policy_id: PolicyId,
  stt_name: ByteArray,
  script_addr: Address
) -> Bool {
  when redeemer is {
    InitElection -> {

      // This is currently true, but remember to remove it if we run into a
      // use case for opening a channel starting from another script.
      // TODO remove anyway, since it's not technically required?
      expect None = datum

      expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
      expect InlineDatum(new_datum) = stt_output.datum
      expect new_state: AdminChannelState = new_datum
      let pub_signed = tx_signed_by(self, new_state.admin) ?
      let new_records_empty = (list.length(new_state.new_records) == 0) ?
      let seq_zero = (new_state.seq == 0) ?
      and {
        pub_signed,
        new_records_empty,
        seq_zero
      }
    }

    AddSubChannels { .. } -> { todo @"add subchannels" }
    RmSubChannels  { .. } -> { todo  @"rm subchannels" }

    EndElection -> {
      expect Some(AdminChannelState { admin, .. }) = datum
      let pub_signed = tx_signed_by(self, admin) ?
      pub_signed
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
      RegularAct(_) -> False // regular actions don't mint or burn
    }
  }

  spend(
    datum: Option<ChannelState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {

    let stt_name = get_stt_name(datum)
    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address

    when redeemer is {
      AdminAct(admin_act) -> {
        // for admin action:
        // - may have none, or some prev admin channel state
        // - but may not have prev subchannel state
        let admin_state: Option<AdminChannelState> = extract_admin_state(datum)
        validate_admin_spend(admin_state, admin_act, self, policy_id, stt_name, script_addr)
      }
      RegularAct(reg_act) -> {
        // for regular action:
        // - may have admin or subchannel state
        // - but must have some prev channel state
        expect Some(state) = datum
        validate_regular_spend(state, reg_act, self, policy_id, stt_name, script_addr)
      }
    }
  }

}
