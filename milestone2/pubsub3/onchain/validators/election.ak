use aiken/primitive/bytearray
use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId}
use config

use election/action.{
  ElectionAction, AdminAct, RegularAct,
  AdminAction, OpenChannel, CloseChannel,
  RegularAction, PostPublicRecords,
  extract_admin_action,
}
use election/record.{validate_records}
use election/state.{
  ChannelState,
  AdminChannel, AdminChannelState,
  SubChannel, SubChannelState,
  extract_admin_state, get_stt_name
}
use election/utils.{tx_mints, tx_does_not_mint, tx_signed_by, tx_sends_token_to_addr}

// TODO will mint() be called when a non-admin tries to post public records too?
pub fn validate_admin_mint(
  action: AdminAction, // RegularActions don't mint or burn
  policy_id: PolicyId,
  self: Transaction,
  oneshot_ref: OutputReference
) -> Bool {
  let stt_name = bytearray.concat(config.stt_prefix, "-admin-channel")
  when action is {
    CloseChannel -> {
      let stt_burned = tx_mints(self, policy_id, stt_name, -1) ?
      stt_burned
    }
    OpenChannel -> {
      expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
      let stt_minted = tx_mints(self, policy_id, stt_name, 1) ?
      stt_minted
    }
    // TODO any need to handle other cases here?
    // TODO extract this part into another fn?
    // TODO is this ever called
    // RegularAction(PostPublicRecords { .. }) -> {
    //   let no_mints = tx_does_not_mint(self, policy_id) ?
    //   no_mints
    // }
  }
}

pub fn validate_regular_spend(
  datum: ChannelState,
  redeemer: RegularAction,
  // own_ref: OutputReference,
  self: Transaction,
  policy_id: PolicyId,
  stt_name: ByteArray,
  script_addr: Address,
) -> Bool {

  // regular actions must always preserve the STT
  expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
  expect InlineDatum(new_datum) = stt_output.datum

  when redeemer is {
    PostPublicRecords -> {

      // TODO can the redundant checks in these branches be DRYed up?
      when datum is {
        AdminChannel(AdminChannelState { admin, seq, .. }) -> {
          expect new_state: AdminChannelState = new_datum
          let pub_signed = tx_signed_by(self, admin) ?
          let pub_unchanged = new_state.admin == admin
          let seq_incremented = (new_state.seq == seq + 1) ?
          let new_records_valid = validate_records(new_state.new_records) ?
          and {
            pub_signed,
            pub_unchanged,
            seq_incremented,
            new_records_valid
          }
        }
        SubChannel(SubChannelState { publisher, seq, .. }) -> {
          expect new_state: SubChannelState = new_datum
          let pub_signed = tx_signed_by(self, publisher) ?
          let pub_unchanged = new_state.publisher == publisher
          let seq_incremented = (new_state.seq == seq + 1) ?
          let new_records_valid = validate_records(new_state.new_records) ?
          and {
            pub_signed,
            pub_unchanged,
            seq_incremented,
            new_records_valid
          }
        }
      }

    }
  }
}

pub fn validate_admin_spend(
  datum: Option<AdminChannelState>,
  redeemer: ElectionAction,
  // own_ref: OutputReference,
  self: Transaction,
  policy_id: PolicyId,
  stt_name: ByteArray, // TODO only pass the prefix, and concat on our own channel id
  script_addr: Address
) -> Bool {
  expect AdminAct(admin_act) = redeemer
  when admin_act is {
      OpenChannel -> {

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

      CloseChannel -> {
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
      AdminAct(action) -> {
        validate_admin_mint(action, policy_id, self, oneshot_ref)
      }
      RegularAct(_) -> False // subchannel publishers don't mint or burn anything
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
        // for admin action, must also have admin channel state
        let admin_state: Option<AdminChannelState> = extract_admin_state(datum)
        validate_admin_spend(admin_state, AdminAct(admin_act), self, policy_id, stt_name, script_addr)
      }
      RegularAct(regular_act) -> {
        // for regular action, could have admin or subchannel state
        expect Some(channel_state) = datum
        validate_regular_spend(channel_state, regular_act, self, policy_id, stt_name, script_addr)
      }
    }
  }

}
