// Second integration test: simplest happy path through the lifecycle of a subchannel.
// Builds on the admin channel tests in validators/tests/integration/minimal.tests.ak.

// use aiken/primitive/string
use cardano/transaction.{Input, Output, OutputReference, Transaction}
// TODO can't import test modules? use tests/integration/happy_adminchannel
use election/action as ea
use election/phase as ep
use election/state.{AdminChannelState, SubChannelState}
use tests/mock

// ===============================
// minimal mint
// ===============================

const admin_pre_add_state = AdminChannelState {
  admin: mock.admin_vkh(),
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigOnboardingPhase),
  seq: 2 // doesn't matter as long as it increases each step
}

const subchannel_id = "guardian1"

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

const add_action = ea.AddSubChannels {
  channels: [subchannel_id]
}

test happy_subchannel_minimal_add() {
  mock.election_validate(add_tx(), add_action)
}

// ===============================
// minimal burn
// ===============================

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

const rm_action = ea.RmSubChannels { channels: [subchannel_id] }

test happy_subchannel_minimal_rm() {
  mock.election_validate(rm_tx(), rm_action)
}
