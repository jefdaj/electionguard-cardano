// OLD CODE
// use cardano/address
// use cardano/assets
// use cardano/assets.{PolicyId}
// use cardano/transaction.{Transaction, Input, Output, OutputReference, NoDatum}
// use election
// use election/types.{ChannelState, OpenChannel}
// use election/utils as u
//
// const state1: ChannelState =
//   ChannelState { publisher: #"00000000000000000000000000000000000000000000000000000000" }
// 
// const oneshot_hash: ByteArray = #"1234"
// 
// const oneshot_utxo: OutputReference =
//   OutputReference { transaction_id: "", output_index: 0 }
// 
// const oneshot_input: Input =
//   Input {
//     output_reference: oneshot_utxo,
//     output: Output {
//       address: address.from_verification_key(#"00"), // any valid address
//       value: assets.from_lovelace(2_000_000),  // 2 ADA
//       datum: NoDatum,
//       reference_script: None,
//     }
//   }
// 
// test open_channel() {
// 
//   // expect Script(oneshot_policy) = u.scriptAddress(oneshot_hash)
// 
//   election.election.mint(
// 
//     /// script parameters
//     "open_channel test nft",
//     oneshot_utxo,
// 
//     /// mint args
//     OpenChannel,
//     oneshot_hash, // TODO have to make this match the oneshot_utxo right?
//     Transaction {
//       ..transaction.placeholder,
//       inputs: [oneshot_input],
//       extra_signatories: [state1.publisher]
//     },
// 
//   )
// }
//
// TODO can mint and spend be tested together, or are they two tests?
