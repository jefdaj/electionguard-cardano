use cardano/address.{Address}
use cardano/assets.{PolicyId}
use cardano/transaction.{OutputReference, Transaction}
use pubsub
use pubsub/types.{PubsubConfig, PsOpen}
use pubsub/utils as u

const cfg1: PubsubConfig =
  PubsubConfig { publisher: #"00000000000000000000000000000000000000000000000000000000" }

const oneshot_hash: ByteArray = #"1234"

const oneshot_utxo: OutputReference =
  OutputReference { transaction_id: "", output_index: 0 }


test open_channel() {
  // expect Script(oneshot_policy) = u.scriptAddress(oneshot_hash)
  pubsub.pubsub.mint(
    /// script parameters
    "open_channel test nft",
    oneshot_utxo,
    /// mint args
    PsOpen,
    oneshot_hash, // TODO have to make this match the oneshot_utxo right?
    Transaction {
      ..transaction.placeholder,
      extra_signatories: [cfg1.publisher]
    },
  )
}

/// TODO can mint and spend be tested together, or are they two tests?
