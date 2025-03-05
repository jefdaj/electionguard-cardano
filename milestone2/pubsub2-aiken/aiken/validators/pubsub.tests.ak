use cardano/transaction.{OutputReference, Transaction}
use pubsub
use pubsub/types.{PubsubConfig, PsOpen}

test open_channel() {

  // TODO how to put datum.owner as publisher? need to create datum first?
  let datum =
    PubsubConfig { publisher: #"00000000000000000000000000000000000000000000000000000000" }
 
  let placeholder_utxo = OutputReference { transaction_id: "", output_index: 0 }

  pubsub.pubsub.spend(

    /// TODO parameters to the validator go here?
    "test channel 1",
    placeholder_utxo, 

    /// followed by regular args:
    Some(datum),
    PsOpen,
    placeholder_utxo,
    Transaction {
      ..transaction.placeholder,
      extra_signatories: [datum.publisher]
    },

  )

}
