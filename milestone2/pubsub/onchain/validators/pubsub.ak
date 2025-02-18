use cardano/assets.{PolicyId}
use cardano/transaction.{Transaction, OutputReference}
use cardano/script_context.{ScriptContext}
use aiken/collection/list

use pubsub/types.{PubsubDatum, PubsubAction, PsOpen, PsFund, PsPublish, PsClose}

validator pubsub {

  mint(redeemer: PubsubAction, _policy_id: PolicyId, _self: Transaction) {
    when redeemer is {
      PsOpen -> True
      _ -> fail
    }
  }

  spend(datum: Option<PubsubDatum>, redeemer: PubsubAction, _utxo: OutputReference, self: Transaction) {
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
