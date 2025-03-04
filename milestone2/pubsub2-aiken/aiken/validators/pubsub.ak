use aiken/collection/list
use cardano/address.{Script}
use cardano/assets.{PolicyId}
use cardano/script_context.{ScriptContext}
use cardano/transaction.{OutputReference, Transaction}
use pubsub/helpers as h
use pubsub/types.{
  PsClose, PsCollect, PsOpen, PsPublish, PubsubAction, PubsubDatum,
}

/// TODO is including the required name and amount here valid?
/// TODO hardcode token name? "pubsub channel NFT" or similar
validator pubsub(token_name: ByteArray, oneshot_ref: OutputReference) {
  mint(redeemer: PubsubAction, policy_id: PolicyId, self: Transaction) {
    when redeemer is {
      PsOpen -> {
        expect Some(_own_input) = h.find_tx_input(self, oneshot_ref)
        h.tx_mints(self, policy_id, token_name, 1)
      }
      PsClose -> h.tx_mints(self, policy_id, token_name, -1)
      _ -> fail
    }
  }

  spend(
    datum: Option<PubsubDatum>,
    redeemer: PubsubAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {
    expect Some(PubsubDatum { publisher }) = datum
    when redeemer is {
      PsOpen -> {
        let Transaction { inputs, .. } = self
        /// TODO None during PsOpen?
        expect Some(own_input) = h.find_tx_input(self, own_ref)
        expect Script(policy_id) = own_input.output.address.payment_credential
        and {
          h.tx_mints(self, policy_id, token_name, 1),
          h.tx_signed_by(self, publisher),
        }
      }
      PsPublish { cids } -> and {
          h.tx_signed_by(self, publisher),
          list.length(cids) > 0,
          todo @"cids are the right format",
          todo @"an output goes back to validator addr",
          todo @"validator output gets the state nft",
          todo @"publisher is unchanged",
        }
      PsCollect -> and {
          h.tx_signed_by(self, publisher),
          todo @"datum goes back to the validator unchanged",
          todo @"all collected assets go to the publisher",
        }
      PsClose -> and {
          h.tx_signed_by(self, publisher),
          todo @"all collected assets go to the publisher",
        }
    }
  }

  /// TODO can this be asserted once at the top?
  /// seems wrong: todo @"datum is none"
  else(_ctx: ScriptContext) {
    fail
  }
}
