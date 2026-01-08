use cardano/transaction.{InlineDatum, OutputReference, Transaction, find_input}
use cardano/address.{Script}
use cardano/assets.{PolicyId}
use config
use pubsub/types.{
  PubsubConfig, PubsubAction, PsOpen, PsPublish, PsClose,
  validate_cids
}
use pubsub/utils.{tx_mints, tx_signed_by, tx_sends_token_to_addr}

validator pubsub(oneshot_ref: OutputReference) {

  mint(
    redeemer: PubsubAction,
    policy_id: PolicyId,
    self: Transaction
  ) {
    when redeemer is {
      PsOpen  -> {
        expect Some(_oneshot_input) = self.inputs |> find_input(oneshot_ref)
        let stt_minted = tx_mints(self, policy_id, config.stt_name, 1) ?
        stt_minted
      }
      PsPublish { .. } -> fail
      PsClose -> {
        let stt_burned = tx_mints(self, policy_id, config.stt_name, -1) ?
        stt_burned
      }
    }
  }

  spend(
    datum: Option<PubsubConfig>,
    redeemer: PubsubAction,
    own_ref: OutputReference,
    self: Transaction,
  ) {

    expect Some(PubsubConfig { publisher }) = datum
    expect Some(own_input) = self.inputs |> find_input(own_ref)
    expect Script(policy_id) = own_input.output.address.payment_credential
    let script_addr = own_input.output.address
    when redeemer is {

      PsOpen -> {
        let pub_signed = tx_signed_by(self, publisher) ?
        let stt_minted = tx_mints(self, policy_id, config.stt_name, 1) ?
        expect Some(_stt_output) = tx_sends_token_to_addr(self, policy_id, config.stt_name, script_addr, 1)
        and {
          pub_signed,
          stt_minted // TODO could this be removed, since mint() checks it too?
        }
      }

      PsPublish { cids } -> {
        let pub_signed = tx_signed_by(self, publisher) ?
	let cids_valid = validate_cids(cids) ?

	// Make sure publisher is unchanged
	// TODO factor out into a util function
        expect Some(stt_output) = tx_sends_token_to_addr(self, policy_id, config.stt_name, script_addr, 1)
	expect InlineDatum(raw_datum) = stt_output.datum
	expect out_config: PubsubConfig = raw_datum
	let same_publisher = (out_config.publisher == publisher) ?

        and {
          pub_signed,
	  cids_valid,
	  same_publisher
        }
      }

      PsClose -> {
        let pub_signed = tx_signed_by(self, publisher) ?
        let stt_burned = tx_mints(self, policy_id, config.stt_name, -1) ?
        and {
          pub_signed,
          stt_burned
        }
      }

    }
  }

}

// OLD CODE
// use aiken/collection/list
// use cardano/address.{Script}
// use cardano/assets.{PolicyId}
// use cardano/script_context.{ScriptContext}
// use cardano/transaction
// use cardano/transaction.{OutputReference, Transaction}
// use pubsub/utils as u
// use pubsub/types.{
//   PsClose, PsOpen, PubsubAction, PubsubConfig,
// }
// 
// // TODO publisher isn't necessarily owner of ADA when doing multi-tiered channels
// 
// validator pubsub(channel_name: ByteArray, oneshot_ref: OutputReference) {
// 
//   mint(redeemer: PubsubAction, policy_id: PolicyId, self: Transaction) {
//     when redeemer is {
// 
//       // Only the publisher can mint the channel_nft,
//       // and only during the initial deployment (enforced via oneshot_ref).
//       // TODO let a separate admin own and mint it? or similar mechanism
//       PsOpen -> {
//         // expect Some(_oneshot_input) = transaction.find_input(self.inputs, oneshot_ref)
//         u.tx_mints(self, policy_id, channel_name, 1)
//       }
// 
//       // Only the publisher can burn the channel_nft,
//       // but they can do it any time.
//       PsClose -> u.tx_mints(self, policy_id, channel_name, -1)
// 
//       // _ -> fail
//     }
//   }
// 
//   // TODO can the open and close cases be delegated to the mint fn here?
//   spend(
//     datum: Option<PubsubConfig>,
//     redeemer: PubsubAction,
//     own_ref: OutputReference,
//     self: Transaction,
//   ) {
//     expect Some(PubsubConfig { publisher }) = datum
//     when redeemer is {
// 
//       PsOpen -> {
//         // Publisher mints channel_nft and sends it to the script.
//     // TODO along with some ADA?
// 
//         // Must use the oneshot_ref as an input.
//         // expect True = list.any(
//         //   self.inputs,
//         //   fn(i) { i.output_reference == oneshot_ref }
//         // )
//     expect Some(_oref) = u.find_tx_input(self, oneshot_ref)
// 
//         // expect Some(own_input) = transaction.find_input(self.inputs, own_ref)
//         expect Some(own_input) = u.find_tx_input(self, own_ref)
//         expect Script(policy_id) = own_input.output.address.payment_credential
// 
//         // TODO Must send the NFT back to our own script address.
// 
//         and {
//       // TODO is this redundant since it's already checked in mint() above?
//           u.tx_mints(self, policy_id, channel_name, 1),
// 
//       // TODO allow admin to open channel for separate publisher
//           u.tx_signed_by(self, publisher),
//         }
// 
//       }
// 
//       // PsCollect ->
//           // u.tx_signed_by(self, publisher)
//           /// todo @"datum goes back to the validator unchanged",
//           /// todo @"all collected assets go to the publisher",
// 
// 
//       // This is kept intentionally minimal for now, because I don't want bugs
//       // interfering with burning all the test NFTs.
//       PsClose -> {
// 
//         // TODO this is redundant because it's already checked in the mint, right?
//         // expect Some(own_input) = u.find_tx_input(self, own_ref)
//         // expect Script(policy_id) = own_input.output.address.payment_credential
//         // and {
//           // u.tx_mints(self, policy_id, channel_name, -1),
//           // u.tx_signed_by(self, publisher),
//         // }
// 
//         u.tx_signed_by(self, publisher)
// 
//         // todo @"all collected assets go to the publisher",
// 
//       }
// 
//     }
//   }
// 
//   // TODO can this be asserted once at the top?
//   // seems wrong: todo @"datum is none"
//   else(_ctx: ScriptContext) {
//     fail
//   }
// }
