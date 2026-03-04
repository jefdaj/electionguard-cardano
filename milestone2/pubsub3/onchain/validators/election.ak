use aiken/primitive/bytearray
use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script}
use cardano/assets.{PolicyId}
use config

use election/action.{ElectionAction, OpenChannel, PostPublicRecords, CloseChannel}
use election/record.{validate_records}
use election/state.{ElectionState}
use election/utils.{tx_mints, tx_does_not_mint, tx_signed_by, tx_sends_token_to_addr}

validator election(oneshot_ref: OutputReference) {

  mint(
    redeemer: ElectionAction,
    policy_id: PolicyId,
    self: Transaction
  ) {
    let stt_name = bytearray.concat(config.stt_prefix, "-admin-channel")
    when redeemer is {
      OpenChannel  -> {
        expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
        let stt_minted = tx_mints(self, policy_id, stt_name, 1) ?
        stt_minted
      }
      PostPublicRecords { .. } -> {
        let no_mints = tx_does_not_mint(self, policy_id) ?
        no_mints
      }
      CloseChannel -> {
        let stt_burned = tx_mints(self, policy_id, stt_name, -1) ?
        stt_burned
      }
    }
  }

  spend(
    datum: Option<ElectionState>,
    redeemer: ElectionAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {

    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address
    let stt_name = bytearray.concat(config.stt_prefix, "-admin-channel")
    when redeemer is {

      OpenChannel -> {

	// This is currently true, but remember to remove it if we run into a
	// use case for opening a channel starting from another script.
	// TODO remove anyway, since it's not technically required?
	expect None = datum

        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
        expect InlineDatum(new_datum) = stt_output.datum
        expect new_cfg: ElectionState = new_datum
        let pub_signed = tx_signed_by(self, new_cfg.publisher) ?
	let new_records_empty = (list.length(new_cfg.new_records) == 0) ?
	let seq_zero = (new_cfg.seq == 0) ?
        and {
          pub_signed,
	  new_records_empty,
	  seq_zero
        }
      }

      PostPublicRecords -> {
        expect Some(ElectionState { publisher, seq, .. }) = datum
        let pub_signed = tx_signed_by(self, publisher) ?
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, stt_name, script_addr, 1)
        expect InlineDatum(new_datum) = stt_output.datum
        expect new_cfg: ElectionState = new_datum
        let pub_unchanged = (new_cfg.publisher == publisher) ?
	let seq_incremented = (new_cfg.seq == seq + 1) ?
        let new_records_valid = validate_records(new_cfg.new_records) ?
        and {
          pub_signed,
          pub_unchanged,
          seq_incremented,
          new_records_valid
        }
      }

      CloseChannel -> {
        expect Some(ElectionState { publisher, .. }) = datum
        let pub_signed = tx_signed_by(self, publisher) ?
        pub_signed
	// TODO require ADA goes back to publisher or main channel
      }

    }
  }

}
