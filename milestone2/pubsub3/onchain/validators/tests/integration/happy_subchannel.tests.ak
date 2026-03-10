// Second integration test: simplest happy path through the lifecycle of a subchannel.
// Builds on the admin channel tests in validators/tests/integration/minimal.tests.ak.

use cardano/transaction.{Input, Output, OutputReference, Transaction}
// TODO can't import test modules? use tests/integration/happy_adminchannel
use election/action as ea
use election/phase as ep
use election/state.{AdminChannelState}
use tests/mock

// ===============================
// minimal mint
// ===============================

const admin_pre_add_state = AdminChannelState {
  admin: mock.admin_vkh(),
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigOnboardingPhase),
  seq: 2 // doesn't really matter as long as it increases
}

const subchannel_id = "guardian1"

const admin_post_add_state = AdminChannelState {
  ..admin_pre_add_state,
  subchannels: [subchannel_id],
  seq: admin_pre_add_state.seq + 1
}

const admin_pre_add_output = Output {
  address: mock.script_address(),
  value: mock.admin_stt_value(),
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

const admin_post_add_output = Output {
  address: mock.script_address(),
  value: mock.admin_stt_value(),
  datum: mock.admin_datum(admin_post_add_state),
  reference_script: None,
}

const add_tx = Transaction {
  ..transaction.placeholder,
  inputs: [admin_pre_add_input],
  outputs: [admin_post_add_output],
  extra_signatories: [mock.admin_vkh()],
}

const add_action = ea.AddSubChannels { channels: [subchannel_id] }

test happy_subchannel_minimal_mint() {
  mock.election_validate(add_tx, add_action)
}

// ===============================
// minimal burn
// ===============================

// TODO merge back into: (9, ep.ElectionFinalizePhase                        ),

test happy_subchannel_minimal_burn() {
  True
}
