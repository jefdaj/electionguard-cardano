use cardano/transaction.{OutputReference, Transaction}
use cardano/assets.{PolicyId}
use config
use pubsub/types.{
  PubsubConfig, PubsubAction, PsOpen, PsClose
}
use pubsub/utils as utils

validator pubsub(oneshot_ref: OutputReference) {

  mint(
    redeemer: PubsubAction,
    policy_id: PolicyId,
    self: Transaction
  ) {
    when redeemer is {
      PsOpen  -> {
        expect Some(_oneshot_input) = transaction.find_input(self.inputs, oneshot_ref)
        utils.tx_mints(self, policy_id, config.stt_name,  1)
      }
      PsClose -> utils.tx_mints(self, policy_id, config.stt_name, -1)
    }
  }

  spend(
    datum: Option<PubsubConfig>,
    redeemer: PubsubAction,
    _own_ref: OutputReference,
    self: Transaction,
  ) {
    expect Some(PubsubConfig { publisher }) = datum
    when redeemer is {
      PsOpen  -> utils.tx_signed_by(self, publisher)
      PsClose -> utils.tx_signed_by(self, publisher)
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
// 	// TODO along with some ADA?
// 
//         // Must use the oneshot_ref as an input.
//         // expect True = list.any(
//         //   self.inputs,
//         //   fn(i) { i.output_reference == oneshot_ref }
//         // )
// 	expect Some(_oref) = u.find_tx_input(self, oneshot_ref)
// 
//         // expect Some(own_input) = transaction.find_input(self.inputs, own_ref)
//         expect Some(own_input) = u.find_tx_input(self, own_ref)
//         expect Script(policy_id) = own_input.output.address.payment_credential
// 
//         // TODO Must send the NFT back to our own script address.
// 
//         and {
// 	  // TODO is this redundant since it's already checked in mint() above?
//           u.tx_mints(self, policy_id, channel_name, 1),
// 
// 	  // TODO allow admin to open channel for separate publisher
//           u.tx_signed_by(self, publisher),
//         }
// 
//       }
// 
//       // PsPublish { cids } -> and {
// 
//       //  u.tx_signed_by(self, publisher),
//       //  list.length(cids) > 0,
//         /// todo @"cids are the right format",
//         /// todo @"an output goes back to validator addr",
//         /// todo @"validator output gets the state nft",
//         /// todo @"publisher is unchanged",
// 
//       //}
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
