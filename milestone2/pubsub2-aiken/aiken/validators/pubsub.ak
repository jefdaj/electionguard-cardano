use aiken/collection/list
use aiken/collection/dict
use cardano/assets.{PolicyId}
use cardano/address.{Script}
use cardano/script_context.{ScriptContext}
use cardano/transaction.{OutputReference, Transaction}
use pubsub/helpers as h
use pubsub/types.{PsClose, PsCollect, PsOpen, PsPublish, PubsubAction, PubsubDatum}

fn must_include_input(tx: Transaction, oref: OutputReference) -> Bool {
  let Transaction { inputs, .. } = tx
  expect Some(_) = list.find(inputs, fn(i) {i.output_reference == oref})
  True
}

fn must_mint(
    tx: Transaction,
    policy_id: PolicyId,
    token_name: ByteArray,
    amount: Int
  ) -> Bool {
  let Transaction { mint, .. } = tx
  /// TODO is including the required name and amount here valid?
  expect [Pair(actual_name, actual_amount)] =
    mint
      |> assets.tokens(policy_id)
      |> dict.to_pairs()
  actual_name == token_name && actual_amount == amount
}

/// TODO hardcode token name? "pubsub channel NFT" or similar
validator pubsub(token_name: ByteArray, oneshot_ref: OutputReference) {

  mint(redeemer: PubsubAction, policy_id: PolicyId, self: Transaction) {
    when redeemer is {
      PsOpen ->
	must_mint(self, policy_id, token_name, 1) &&
	must_include_input(self, oneshot_ref)
      PsClose ->
        must_mint(self, policy_id, token_name, -1)
      _ -> fail
    }
  }

  spend(
    datum: Option<PubsubDatum>,
    redeemer: PubsubAction,
    utxo: OutputReference,
    self: Transaction,
  ) {
    expect Some(PubsubDatum { publisher }) = datum /// TODO None during PsOpen?
    when redeemer is {
      PsOpen -> {
        let Transaction { inputs, .. } = self
        expect Some(own_input) = list.find(inputs, fn(i) { i.output_reference == utxo })
        expect Script(policy_id) = own_input.output.address.payment_credential
	must_mint(self, policy_id, token_name, 1) &&
        h.signed(self, publisher) /// TODO can this be asserted once at the top?
      }
      PsPublish { cids } -> and {
        h.signed(self, publisher),
        list.length(cids) > 0,
	todo @"cids are the right format",
	todo @"an output goes back to validator addr",
	todo @"validator output gets the state nft",
	todo @"publisher is unchanged",
      }
      PsCollect -> and {
        h.signed(self, publisher),
	todo @"datum goes back to the validator unchanged",
	todo @"all collected assets go to the publisher",
      }
      PsClose -> and {
        h.signed(self, publisher),
	todo @"all collected assets go to the publisher",
	/// seems wrong: todo @"datum is none"
      }
    }
  }

  else(_ctx: ScriptContext) {
    fail
  }

}
