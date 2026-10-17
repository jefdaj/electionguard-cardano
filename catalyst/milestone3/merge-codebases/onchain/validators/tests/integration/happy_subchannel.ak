// Second integration test: simplest happy path through the lifecycle of a subchannel.
// Builds on the admin channel tests in validators/tests/integration/minimal.tests.ak.

use aiken/primitive/string
use aiken/primitive/bytearray
use aiken/collection/list
use cardano/transaction.{Input, Output, OutputReference, Transaction}
// TODO can't import test modules? use tests/integration/happy_adminchannel
use election/types/action as ea
use election/types/phase as ep
use election/types/channel.{AdminChannelState, SubChannelState}
use tests/mock

// ===============================
// add single subchannel
// ===============================

pub const subchannel_id = string.to_bytearray(@"guardian1")

const add_action = ea.AddSubChannels { channels: [subchannel_id] }

pub const admin_pre_add_state = AdminChannelState {
  admin: mock.admin_vkh,
  ipfs_node: None,
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigOnboardingPhase),
  seq: 2 // doesn't matter as long as it increments each step
}

const admin_pre_add_output = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_pre_add_state),
  reference_script: None,
}

pub const admin_pre_add_input = Input {
  output_reference: OutputReference {
    transaction_id: "abc1",
    output_index: 0,
  },
  output: admin_pre_add_output,
}

pub const admin_post_add_state = AdminChannelState {
  ..admin_pre_add_state,
  subchannels: [subchannel_id],
  seq: admin_pre_add_state.seq + 1
}

const admin_post_add_output = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_post_add_state),
  reference_script: None,
}

pub const sub_post_add_state = SubChannelState {
  channel_id: subchannel_id,
  publisher: mock.vkh(subchannel_id),
  ipfs_node: None,
  new_records: [],
  seq: 0,
}

const sub_post_add_output = Output {
  address: mock.script_address(),
  value: mock.stt_value(subchannel_id),
  datum: mock.subchannel_datum(sub_post_add_state),
  reference_script: None,
}

fn add_tx() -> Transaction {
  let mint_val = mock.mint_stt(subchannel_id)
  Transaction {
    ..transaction.placeholder,
    inputs: [admin_pre_add_input],
    mint: mint_val,
    outputs: [
      admin_post_add_output,
      sub_post_add_output,
      mock.collateral(subchannel_id),
    ],
    extra_signatories: [mock.admin_vkh],
  }
}

pub fn test_single_add() {
  mock.election_validate(add_tx(), add_action)
}

// ===============================
// rm single subchannel
// ===============================

const rm_action = ea.RmSubChannels { channels: [subchannel_id] }

const admin_pre_rm_state = AdminChannelState {
  admin: mock.admin_vkh,
  ipfs_node: None,
  subchannels: [subchannel_id],
  new_records: [],
  phase: ep.ElectionFinalizePhase,
  seq: 10 // doesn't matter as long as it increases each step
}

const admin_post_rm_state = AdminChannelState {
  ..admin_pre_rm_state,
  subchannels: [],
  seq: admin_pre_rm_state.seq + 1,
}

const admin_post_rm_output = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_post_rm_state),
  reference_script: None,
}

const admin_pre_rm_output = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_pre_rm_state),
  reference_script: None,
}

pub const admin_pre_rm_input = Input {
  output_reference: OutputReference {
    transaction_id: "abc2",
    output_index: 0,
  },
  output: admin_pre_rm_output,
}

pub const sub_post_add_input = Input {
  output_reference: OutputReference {
    transaction_id: "def1",
    output_index: 1, // TODO is this right? does it matter?
  },
  output: sub_post_add_output,
}

fn rm_tx() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    inputs: [admin_pre_rm_input, sub_post_add_input],
    mint: mock.burn_stt(subchannel_id),
    outputs: [admin_post_rm_output],
    extra_signatories: [mock.admin_vkh],
  }
}

pub fn test_single_rm() {
  mock.election_validate(rm_tx(), rm_action)
}

// ===============================
// add multiple subchannels
// ===============================

const subchannel_ids_unsorted = [
  "guardian1", "guardian2", "guardian3",
  "device1", "device2",
  "verifier1", "verifier2", "verifier3"
]

const subchannel_ids = list.sort(subchannel_ids_unsorted, bytearray.compare)

const add_action_multi = ea.AddSubChannels { channels: subchannel_ids }

const admin_post_add_state_multi = AdminChannelState {
  ..admin_pre_add_state,
  subchannels: subchannel_ids,
  seq: admin_pre_add_state.seq + 1
}

const admin_post_add_output_multi = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_post_add_state_multi),
  reference_script: None,
}

const sub_post_add_states_multi =
  list.map(
    subchannel_ids,
    fn(sub_id) {
      SubChannelState {
        channel_id: sub_id,
        publisher: mock.vkh(subchannel_id),
        ipfs_node: None,
        new_records: [],
        seq: 0,
      }
    }
  )

const sub_post_add_outputs_multi =
  list.map(
    sub_post_add_states_multi,
    fn(sub_state) {
      Output {
        address: mock.script_address(),
        value: mock.stt_value(sub_state.channel_id),
        datum: mock.subchannel_datum(sub_state),
        reference_script: None,
      }
    }
  )

const sub_collateral_outputs = list.map(subchannel_ids, mock.collateral)

fn add_tx_multi() -> Transaction {
  let mint_val = mock.mint_stts(subchannel_ids)
  let outputs = [admin_post_add_output_multi]
    |> list.concat(sub_post_add_outputs_multi)
    |> list.concat(sub_collateral_outputs)
  Transaction {
    ..transaction.placeholder,
    inputs: [admin_pre_add_input],
    mint: mint_val,
    outputs: outputs,
    extra_signatories: [mock.admin_vkh],
  }
}

pub fn test_multi_add() {
  mock.election_validate(add_tx_multi(), add_action_multi)
}

// ===============================
// rm multiple subchannels
// ===============================

const rm_action_multi = ea.RmSubChannels { channels: subchannel_ids }

pub fn sub_pre_rm_inputs_multi() -> List<Input> {
  let outputs = sub_post_add_outputs_multi
  list.map(
    outputs,
    fn(output) {
      expect Some(i) = list.index_of(outputs, output)
      let n = i + 1 // zero indexed
      let tx_id = string.to_bytearray(string.concat(@"def", string.from_int(n))) // TODO reverse?
      Input {
        output_reference: OutputReference {
          transaction_id: tx_id,
          output_index: n, // 0 is the admin stt
        },
        output: output,
      }
    }
  )
}

const admin_pre_rm_state_multi = AdminChannelState {
  admin: mock.admin_vkh,
  ipfs_node: None,
  subchannels: subchannel_ids,
  new_records: [],
  phase: ep.ElectionFinalizePhase,
  seq: 10 // doesn't matter as long as it increases each step
}

const admin_pre_rm_output_multi = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_pre_rm_state_multi),
  reference_script: None,
}

const admin_pre_rm_input_multi = Input {
  output_reference: OutputReference {
    transaction_id: "abc2",
    output_index: 0,
  },
  output: admin_pre_rm_output_multi,
}

fn rm_tx_multi() -> Transaction {
  let burn_val = mock.burn_stts(subchannel_ids)
  let sub_inputs = sub_pre_rm_inputs_multi()
  Transaction {
    ..transaction.placeholder,
    inputs: [
      admin_pre_rm_input_multi,
      ..sub_inputs
    ],
    mint: burn_val,
    outputs: [admin_post_rm_output], // TODO can it be the same?
    extra_signatories: [mock.admin_vkh],
  }
}

pub fn test_multi_rm() {
  mock.election_validate(rm_tx_multi(), rm_action_multi)
}
