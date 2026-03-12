// Happy path through a full election, posting statically generated CIDs.
// This one has enough going on that I need variable naming conventions:
//
// 1. first channel name: admin, guardian1, ...
// 2. then txN where N == seq: 0, 1, ...
// 3. type: (s)tate, (in)put, (out)put, ...
// 4. finally an input/output index: 0, 1, ...
//
// Examples:
// - admin_s0
// - device1_tx3_in0
// - device1_tx3_out0
//
// Tests will be named by channel and txN. Examples:
// - happy_election_admin_tx0
// - happy_election_device1_tx3
//

// use tests/data/static_election_records as sr
// use aiken/collection/list
// use aiken/primitive/string
// use aiken/primitive/int
// use cardano/assets
// use cardano/transaction.{Input, NoDatum, Output, OutputReference, Transaction}
use cardano/transaction.{Output, Transaction}
use election/action as ea
use election/phase as ep
use election/state.{AdminChannelState}
use tests/mock

// =================================
// initial solo admin section:
// 1. init election
// 2. announce config
// 3. onboarding (add subchannels)
// =================================
// ====================
// InitElection
// ====================

test happy_election_admin_tx0() {
  mock.election_validate(admin_tx0(), ea.InitElection)
}

fn admin_tx0() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    mint: mock.stt_value("admin"),
    inputs: [mock.oneshot_input()],
    outputs: [admin_tx0_out0()],
  }
}

fn admin_tx0_out0() -> Output {
  Output {
    address: mock.script_address(),
    value: mock.stt_value("admin"),
    datum: mock.admin_datum(admin_s0()),
    reference_script: None,
  }
}

fn admin_s0() -> AdminChannelState {
  AdminChannelState {
    admin: mock.admin_vkh(),
    subchannels: [],
    new_records: [],
    phase: ep.ElectionConfigPhase(ep.ConfigAnnouncePhase),
    seq: 0
  }
}

// =================================
// parallel admin section:
// 1. ceremony
// 2. finalize config (device here?)
// 3. voting
// 4. results tally
// 5. results decrypt
// 6. verify
// =================================

// =================================
// parallel subchannels sections
// (grouped by channel):
// 1. key ceremony
// 2. device announce?
// 3. voting
// 4. results decrypt
// 5. verify
// =================================

// =================================
// final solo admin section:
// 1. rm subchannels
// 2. end election
// =================================
