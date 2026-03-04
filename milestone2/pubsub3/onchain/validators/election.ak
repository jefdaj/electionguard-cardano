use aiken/primitive/bytearray
use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use config

use election/action.{ElectionAction, AdminAction, SubChannelAction, AdminOpenChannel, AdminPostPublicRecords, AdminCloseChannel}
use election/record.{validate_records}
use election/state.{ChannelState, AdminChannelState, extract_admin_state}
use election/utils.{tx_mints, tx_does_not_mint, tx_signed_by, tx_sends_token_to_addr}

pub fn validate_admin_mint(
  action: AdminAction,
  policy_id: PolicyId,
  self: Transaction,
  oneshot_ref: OutputReference
) -> Bool {
  let stt_name = bytearray.concat(config.stt_prefix, "-admin-channel")
  when action is {
    AdminOpenChannel -> {
      expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
      let stt_minted = tx_mints(self, policy_id, stt_name, 1) ?
      stt_minted
    }
    AdminPostPublicRecords { .. } -> {
      let no_mints = tx_does_not_mint(self, policy_id) ?
      no_mints
    }
    AdminCloseChannel -> {
      let stt_burned = tx_mints(self, policy_id, stt_name, -1) ?
      stt_burned
    }
  }
}

pub fn validate_admin_spend(
  datum: Option<AdminChannelState>,
  redeemer: AdminAction,
  // own_ref: OutputReference,
  self: Transaction,
  policy_id: PolicyId,
  stt_name: ByteArray, // TODO only pass the prefix, and concat on our own channel id
  script_addr: Address
) -> Bool {
  when redeemer is {
      AdminOpenChannel -> {

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

      AdminPostPublicRecords -> {
        expect Some(AdminChannelState { admin, seq, .. }) = datum
        let pub_signed = tx_signed_by(self, admin) ?
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
        expect InlineDatum(new_datum) = stt_output.datum
        expect new_state: AdminChannelState = new_datum
        let pub_unchanged = (new_state.admin == admin) ?
        let seq_incremented = (new_state.seq == seq + 1) ?
        let new_records_valid = validate_records(new_state.new_records) ?
        and {
          pub_signed,
          pub_unchanged,
          seq_incremented,
          new_records_valid
        }
      }

      AdminCloseChannel -> {
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
      AdminAction(action) -> validate_admin_mint(action, policy_id, self, oneshot_ref)
      SubChannelAction(_action) -> False // subchannel publishers don't mint or burn anything
    }
  }

  spend(
    datum: Option<ChannelState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {

    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address
    let stt_name = bytearray.concat(config.stt_prefix, "-admin-channel")
    when redeemer is {
      AdminAction(admin_action) -> {
        expect Some(state) = datum
	let admin_state = extract_admin_state(state)
        validate_admin_spend(admin_state, admin_action, self, policy_id, stt_name, script_addr)
      }
      SubChannelAction(_) -> todo @"validate_subchannel_spend"
    }
  }

}
