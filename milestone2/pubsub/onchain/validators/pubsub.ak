use aiken/collection/list
use cardano/assets.{PolicyId}
use cardano/script_context.{ScriptContext}
use cardano/transaction.{OutputReference, Transaction}
use pubsub/types.{PsClose, PsFund, PsOpen, PsPublish, PubsubAction, PubsubDatum}

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
    let publisher_signed = list.has(self.extra_signatories, publisher)
    when redeemer is {
      PsFund -> publisher_signed
      PsPublish { cids } -> and {
          publisher_signed,
          list.length(cids) > 0,
        }
      PsClose -> and {
          publisher_signed,
          todo @"ADA goes back to publisher",
        }
      _ -> fail
    }
  }

  else(_ctx: ScriptContext) {
    fail
  }
}
