// use pubsub/tests as t
use cardano/transaction.{OutputReference, Transaction, placeholder}
use pubsub/types.{PubsubConfig, PubsubAction, PsOpen, PsPublish, PsCollect, PsClose}

test ps_open() {

  // TODO how to put datum.owner as publisher? need to create datum first?
  let datum =
    PubsubConfig { publisher: #"00000000000000000000000000000000000000000000000000000000" }
 
  let placeholder_utxo = OutputReference { transaction_id: "", output_index: 0 }

  // TODO how do you import and parameterize the validator?
  let contract = pubsub("test psopen", placeholder_utxo)
 
  contract.spend(
    Some(datum),
    PsOpen,
    placeholder_utxo,
    Transaction { ..transaction.placeholder, extra_signatories: [datum.owner] },
  )

}
