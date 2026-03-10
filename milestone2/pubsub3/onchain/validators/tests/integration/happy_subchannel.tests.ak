// Second integration test: simplest happy path through the lifecycle of a subchannel.
// Builds on the admin channel tests in validators/tests/integration/minimal.tests.ak.

// use aiken/primitive/string
use aiken/collection/list
use cardano/transaction.{Input, Output, OutputReference, Transaction}
// TODO can't import test modules? use tests/integration/happy_adminchannel
use election/action as ea
use election/phase as ep
use election/state.{AdminChannelState, SubChannelState}
use tests/mock

// ===============================
// add single subchannel
// ===============================

const subchannel_id = "guardian1"

const add_action = ea.AddSubChannels { channels: [subchannel_id] }

const admin_pre_add_state = AdminChannelState {
  admin: mock.admin_vkh(),
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigOnboardingPhase),
  seq: 2 // doesn't matter as long as it increases each step
}

const admin_pre_add_output = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_pre_add_state),
  reference_script: None,
}

const admin_pre_add_input = Input {
  output_reference: OutputReference {
    transaction_id: "abc1",
    output_index: 0,
  },
  output: admin_pre_add_output,
}

const admin_post_add_state = AdminChannelState {
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

const sub_post_add_state = SubChannelState {
  channel_id: subchannel_id,
  publisher: mock.publisher_vkh(),
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
    ],
    extra_signatories: [mock.admin_vkh()],
  }
}

test happy_subchannel_single_add() {
  mock.election_validate(add_tx(), add_action)
}

// ===============================
// rm single subchannel
// ===============================

const rm_action = ea.RmSubChannels { channels: [subchannel_id] }

const admin_pre_rm_state = AdminChannelState {
  admin: mock.admin_vkh(),
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

const admin_pre_rm_input = Input {
  output_reference: OutputReference {
    transaction_id: "abc2",
    output_index: 0,
  },
  output: admin_pre_rm_output,
}

const sub_post_add_input = Input {
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
    outputs: [
      admin_post_rm_output,
    ],
    extra_signatories: [mock.admin_vkh()],
  }
}

test happy_subchannel_single_rm() {
  mock.election_validate(rm_tx(), rm_action)
}

// ===============================
// add multiple subchannels
// ===============================

const subchannel_ids = [
  "guardian1", "guardian2", "guardian3",
  "device1", "device2",
  "verifier1", "verifier2", "verifier3"
]

// const n_subchannels = list.length(subchannel_ids)

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
        publisher: mock.publisher_vkh(),
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

fn add_tx_multi() -> Transaction {
  let mint_val = mock.mint_stts(subchannel_ids)
  Transaction {
    ..transaction.placeholder,
    inputs: [admin_pre_add_input],
    mint: mint_val,
    outputs: [
      admin_post_add_output_multi,
      ..sub_post_add_outputs_multi
    ],
    extra_signatories: [mock.admin_vkh()],
  }
}

test happy_subchannel_multi_add() {
  mock.election_validate(add_tx_multi(), add_action_multi)
}
