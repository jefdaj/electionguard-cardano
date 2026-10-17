// Extend validators/tests/integration/happy_subchannel.ak
// by adding set_ipfs_node in several places.

// use aiken/primitive/string
// use aiken/collection/list
use cardano/transaction.{Output, Transaction}
use election/types/action as ea
// use election/types/phase as ep
use election/types/channel.{AdminChannelState, SubChannelState}

use tests/mock
use tests/unit/ipfs_node as ipfs_node_unit_tests
use tests/integration/happy_subchannel.{
  admin_pre_add_state, admin_pre_add_input,
  sub_post_add_state, sub_post_add_input,
  subchannel_id,
}

const set_action = ea.SetIpfsNode

const new_node = ipfs_node_unit_tests.ipfs_node_valid_no_hints

// ===============================
// set admin ipfs_node
// ===============================

const admin_node_state = AdminChannelState {
  ..admin_pre_add_state,
  ipfs_node: Some(new_node),
  seq: admin_pre_add_state.seq + 1
}

const admin_node_output = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_node_state),
  reference_script: None,
}

fn admin_tx() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    inputs: [admin_pre_add_input],
    outputs: [admin_node_output],
    extra_signatories: [mock.admin_vkh],
  }
}

pub fn test_admin_set_ipfs_node() {
  mock.election_validate(admin_tx(), set_action)
}

//// ===============================
//// set subchannel ipfs_node
//// ===============================


const sub_node_state = SubChannelState {
  ..sub_post_add_state,
  ipfs_node: Some(new_node),
  seq: sub_post_add_state.seq + 1
}

const sub_node_output = Output {
  address: mock.script_address(),
  value: mock.stt_value(subchannel_id),
  datum: mock.subchannel_datum(sub_node_state),
  reference_script: None,
}

fn sub_tx() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    inputs: [sub_post_add_input],
    outputs: [sub_node_output],
    extra_signatories: [mock.vkh(subchannel_id)],
  }
}

pub fn test_sub_set_ipfs_node() {
  mock.election_validate(sub_tx(), set_action)
}
