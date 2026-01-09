use cardano/transaction.{OutputReference, Transaction, find_input}
use cardano/address.{Script}
use cardano/assets.{PolicyId}
use config
use pubsub/types.{
  PubsubConfig, PubsubAction, PsOpen, PsPublish, PsClose,
  validate_cids
}
use pubsub/utils.{tx_mints, tx_does_not_mint, tx_signed_by, tx_sends_token_to_addr, publisher_unchanged}

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

    expect Some(PubsubConfig { publisher }) = datum
    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address
    when redeemer is {

      PsOpen -> {
        let pub_signed = tx_signed_by(self, publisher) ?
        let stt_minted = tx_mints(self, policy_id, config.stt_name, 1) ?
        expect Some(_stt_output) = tx_sends_token_to_addr(self, policy_id, config.stt_name, script_addr, 1)
        and {
          pub_signed,
          stt_minted // TODO could this be removed, since mint() checks it too?
        }
      }

      PsPublish { cids } -> {
        let pub_signed = tx_signed_by(self, publisher) ?
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, config.stt_name, script_addr, 1)
        let pub_unchanged = publisher_unchanged(publisher, stt_output) ?
        let cids_valid = validate_cids(cids) ?
        and {
          pub_signed,
          pub_unchanged,
          cids_valid
        }
      }

      PsClose -> {
        let pub_signed = tx_signed_by(self, publisher) ?
        let stt_burned = tx_mints(self, policy_id, config.stt_name, -1) ?
        and {
          pub_signed,
          stt_burned
        }
      }

    }
  }

}
