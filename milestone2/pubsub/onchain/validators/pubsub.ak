use aiken/collection/list
use cardano/assets.{PolicyId}
use cardano/script_context.{ScriptContext}
use cardano/transaction.{OutputReference, Transaction}
use pubsub/types.{PsClose, PsFund, PsOpen, PsPublish, PubsubAction, PubsubDatum}
use pubsub/helpers as h

validator pubsub {
  mint(redeemer: PubsubAction, _policy_id: PolicyId, _self: Transaction) {
    when redeemer is {
      PsOpen -> todo @"publisher in redeemer matches tx sender"
      _ -> fail
    }
  }

  spend(
    datum: Option<PubsubDatum>,
    redeemer: PubsubAction,
    _utxo: OutputReference,
    self: Transaction,
  ) {
    expect Some(PubsubDatum { publisher }) = datum
    let p_signed = h.signed(self, publisher)
    when redeemer is {
      PsFund -> p_signed
      PsPublish { cids } -> and {
          p_signed,
          list.length(cids) > 0,
        }
      PsClose -> and {
          p_signed,
          todo @"ADA goes back to publisher",
        }
      _ -> fail
    }
  }

  else(_ctx: ScriptContext) {
    fail
  }
}
