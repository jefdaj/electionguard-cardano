use aiken/collection/list
use cardano/assets.{PolicyId}
use cardano/script_context.{ScriptContext}
use cardano/transaction.{OutputReference, Transaction}
use pubsub/types.{PsClose, PsFund, PsOpen, PsPublish, PubsubAction, PubsubDatum}

validator pubsub {
  mint(redeemer: PubsubAction, _policy_id: PolicyId, _self: Transaction) {
    when redeemer is {
      PsOpen -> True
      _ -> fail
    }
  }

  spend(
    datum: Option<PubsubDatum>,
    redeemer: PubsubAction,
    _utxo: OutputReference,
    self: Transaction,
  ) {
    when redeemer is {
      PsFund -> True
      PsPublish { .. } -> {
        expect Some(PubsubDatum { publisher }) = datum
        list.has(self.extra_signatories, publisher)
      }
      PsClose -> True
      _ -> fail
    }
  }

  else(_ctx: ScriptContext) {
    fail
  }
}
