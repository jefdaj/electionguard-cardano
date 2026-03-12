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

// use aiken/collection/list
// use aiken/primitive/int
// use aiken/primitive/string
// use cardano/assets
// use cardano/transaction.{Input, NoDatum, Output, OutputReference, Transaction}
use cardano/transaction.{Transaction}
use election/action as ea
use election/phase as ep
use election/state.{AdminChannelState}
use tests/data/static_election_records as sr
use tests/mock

// =================================
// initial solo admin section:
// 1. init election
// 2. announce config
// 3. onboarding (add subchannels)
// =================================

// ----------- admin_tx0 -----------

const admin_s0 = AdminChannelState {
  admin: mock.admin_vkh(),
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigAnnouncePhase),
  seq: 0
}

const admin_tx0_out0 = mock.script_output("admin", mock.admin_datum(admin_s0))

const admin_tx0 = Transaction {
  ..transaction.placeholder,
  mint: mock.stt_value("admin"),
  inputs: [mock.oneshot_input],
  outputs: [admin_tx0_out0],
}

test happy_election_admin_tx0() {
  mock.election_validate(admin_tx0, ea.InitElection)
}

// ----------- admin_tx1 -----------

const admin_s1 = AdminChannelState {
  admin: mock.admin_vkh(),
  subchannels: [],
  new_records: [
    sr.manifest,
    sr.ceremony_details,
  ],
  phase: ep.ElectionConfigPhase(ep.ConfigOnboardingPhase),
  seq: 1,
}

const admin_tx1_out0 = mock.script_output("admin", mock.admin_datum(admin_s1))

const admin_tx1_in0 = mock.input(@"admin_tx0", 0, admin_tx0_out0)

const admin_tx1 = Transaction {
  ..transaction.placeholder,
  inputs: [admin_tx1_in0],
  outputs: [admin_tx1_out0],
  extra_signatories: [mock.admin_vkh()],
}

test happy_election_admin_tx1() {
  mock.election_validate(admin_tx1, ea.PostPublicRecords)
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
