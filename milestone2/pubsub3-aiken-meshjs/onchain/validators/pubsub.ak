use aiken/collection/list
use cardano/address.{Script}
use cardano/assets.{PolicyId}
use cardano/script_context.{ScriptContext}
use cardano/transaction
use cardano/transaction.{OutputReference, Transaction}
use pubsub/utils as u
use pubsub/types.{
  PsClose, PsOpen, PsPublish, PubsubAction, PubsubConfig,
}

// TODO publisher isn't necessarily owner of ADA when doing multi-tiered channels

validator pubsub(channel_name: ByteArray, oneshot_ref: OutputReference) {
  mint(redeemer: PubsubAction, policy_id: PolicyId, self: Transaction) {
    when redeemer is {
      PsOpen -> {

        // TODO what's wrong with this part?
        // expect Some(_oneshot_input) = transaction.find_input(self.inputs, oneshot_ref)

        u.tx_mints(self, policy_id, channel_name, 1)
      }
      PsClose -> u.tx_mints(self, policy_id, channel_name, -1)
      _ -> fail
    }
  }

  spend(
    datum: Option<PubsubConfig>,
    redeemer: PubsubAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {
    expect Some(PubsubConfig { publisher }) = datum
    when redeemer is {
      PsOpen -> {
        /// TODO None during PsOpen?
        /// expect True = list.any(
        ///   self.inputs,
        ///   fn(i) { i.output_reference == oneshot_ref }
        /// )
        /// expect Some(own_input) = transaction.find_input(self.inputs, own_ref)
        expect Some(own_input) = u.find_tx_input(self, own_ref)
        expect Script(policy_id) = own_input.output.address.payment_credential
        and {
          u.tx_mints(self, policy_id, channel_name, 1),
          u.tx_signed_by(self, publisher),
        }
      }
      PsPublish { cids } -> and {
        u.tx_signed_by(self, publisher),
        list.length(cids) > 0,
        /// todo @"cids are the right format",
        /// todo @"an output goes back to validator addr",
        /// todo @"validator output gets the state nft",
        /// todo @"publisher is unchanged",
      }
      // PsCollect ->
          // u.tx_signed_by(self, publisher)
          /// todo @"datum goes back to the validator unchanged",
          /// todo @"all collected assets go to the publisher",
      PsClose -> {

        // TODO this is redundant because it's already checked in the mint, right?
        // expect Some(own_input) = u.find_tx_input(self, own_ref)
        // expect Script(policy_id) = own_input.output.address.payment_credential
        // and {
          // u.tx_mints(self, policy_id, channel_name, -1),
          // u.tx_signed_by(self, publisher),
        // }

        u.tx_signed_by(self, publisher)
        /// todo @"all collected assets go to the publisher",
      }
    }
  }

  /// TODO can this be asserted once at the top?
  /// seems wrong: todo @"datum is none"
  else(_ctx: ScriptContext) {
    fail
  }
}
