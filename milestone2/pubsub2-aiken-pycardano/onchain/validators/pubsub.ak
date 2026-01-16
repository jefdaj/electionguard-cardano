use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction, InlineDatum, find_input}
use cardano/address.{Script}
use cardano/assets.{PolicyId}
use config
use pubsub/types.{
  PubsubConfig, PubsubAction, PsOpen, PsPublish, PsClose,
  validate_cids
}
use pubsub/utils.{tx_mints, tx_does_not_mint, tx_signed_by, tx_sends_token_to_addr}

validator pubsub(oneshot_ref: OutputReference) {

  mint(
    redeemer: PubsubAction,
    policy_id: PolicyId,
    self: Transaction
  ) {
    when redeemer is {
      PsOpen  -> {
        expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
        let stt_minted = tx_mints(self, policy_id, config.stt_name, 1) ?
        stt_minted
      }
      PsPublish { .. } -> {
        let no_mints = tx_does_not_mint(self, policy_id) ?
        no_mints
      }
      PsClose -> {
        let stt_burned = tx_mints(self, policy_id, config.stt_name, -1) ?
        stt_burned
      }
    }
  }

  spend(
    datum: Option<PubsubConfig>,
    redeemer: PubsubAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {

    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address
    when redeemer is {

      PsOpen -> {

        expect None = datum // TODO is this right?

        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, config.stt_name, script_addr, 1)
	// TODO can this be condensed down to Some(PubsubConfig {...}) = stt_output.datum?
        expect InlineDatum(new_datum) = stt_output.datum
        expect new_cfg: PubsubConfig = new_datum
        let pub_signed = tx_signed_by(self, new_cfg.publisher) ?
        let stt_minted = tx_mints(self, policy_id, config.stt_name, 1) ?
	let cids_empty = (list.length(new_cfg.cids) == 0) ?
	let seq_zero   = (new_cfg.seq == 0) ?

        and {
          pub_signed,
          stt_minted, // TODO could this be removed, since mint() checks it too?
	  cids_empty,
	  seq_zero
        }
      }

      PsPublish -> {
        expect Some(PubsubConfig { publisher, seq, .. }) = datum
        let pub_signed = tx_signed_by(self, publisher) ?
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, config.stt_name, script_addr, 1)
        expect InlineDatum(new_datum) = stt_output.datum
        expect new_cfg: PubsubConfig = new_datum
        // let pub_unchanged = publisher_unchanged(publisher, stt_output) ?
        let pub_unchanged = (new_cfg.publisher == publisher) ?
	let seq_incremented = (new_cfg.seq == seq + 1) ?
        let cids_valid = validate_cids(new_cfg.cids) ?
	// TODO test no stt mint here too? or is that redundant?
        and {
          pub_signed,
          pub_unchanged,
          seq_incremented,
          cids_valid
        }
      }

      PsClose -> {
        expect Some(PubsubConfig { publisher, .. }) = datum
        let pub_signed = tx_signed_by(self, publisher) ?
        let stt_burned = tx_mints(self, policy_id, config.stt_name, -1) ?
	// no stt_output when closing
	// TODO does that need an explicit check?
        and {
          pub_signed,
          stt_burned
        }
      }

    }
  }

}
