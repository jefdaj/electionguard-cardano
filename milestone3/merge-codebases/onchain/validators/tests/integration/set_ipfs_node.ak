// Extend validators/tests/integration/happy_subchannel.ak
// by adding set_ipfs_node in several places.

// use aiken/primitive/string
// use aiken/collection/list
// use cardano/transaction.{Input, Output, OutputReference, Transaction}
// use election/types/action as ea
// use election/types/phase as ep
// use election/types/channel.{AdminChannelState, SubChannelState}
// use election/types/ipfs_node.{
  // IpfsNode,
  // validate_peer_id, validate_multiaddr,
  // validate_ipfs_node
// }

// use tests/mock
// use tests/unit/ipfs_node as ipfs_node_unit_tests
// use tests/integration/happy_subchannel.{
  // admin_pre_add_state, admin_post_add_state,
  // subchannel_id, sub_post_add_state,
// }

// const set_action = ea.SetIpfsNode

//const new_node = IpfsNode {
//  peer_id: IpfsPeerId,
//  addr_hints: [],
//}
//
//// ===============================
//// set admin ipfs_node
//// ===============================
//
//const admin_with_node = AdminChannelState {
//  ..admin_pre_add_state,
//  ipfs_node: 
//  seq: admin_pre_add_state.seq + 1
//}
//
//fn add_tx() -> Transaction {
//  let mint_val = mock.mint_stt(subchannel_id)
//  Transaction {
//    ..transaction.placeholder,
//    inputs: [admin_pre_add_input],
//    mint: mint_val,
//    outputs: [
//      admin_post_add_output,
//      sub_post_add_output,
//      mock.collateral(subchannel_id),
//    ],
//    extra_signatories: [mock.admin_vkh],
//  }
//}
//
//pub fn test_single_add() {
//  mock.election_validate(add_tx(), add_action)
//}
//
//
//// ===============================
//// set subchannel ipfs_node
//// ===============================
//
