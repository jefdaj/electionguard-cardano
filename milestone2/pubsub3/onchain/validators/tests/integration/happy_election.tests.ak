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

use aiken/collection/list
// use aiken/primitive/int
// use aiken/primitive/string
use cardano/assets
// use cardano/transaction.{Input, NoDatum, Output, OutputReference, Transaction}
use cardano/transaction.{Transaction, Output}
use election/action as ea
use election/phase as ep
use election/state.{
  ChannelId, channel_id,
  AdminChannelState, SubChannelState
}
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
  admin: mock.admin_vkh,
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

// post 2 records and advance
const admin_s1 = AdminChannelState {
  admin: mock.admin_vkh,
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
  extra_signatories: [mock.admin_vkh],
}

test happy_election_admin_tx1() {
  mock.election_validate(admin_tx1, ea.PostPublicRecords)
}

// ----------- admin_tx2 -----------

const subchannel_ids: List<ChannelId> =
  list.map(
    [@"guardian1", @"guardian2", @"guardian3", @"device1", @"verifier1"],
    channel_id
  )

// TODO is it confusing that you hash the prev tx number here?
const admin_tx2_in0 = mock.input(@"admin_tx1", 0, admin_tx1_out0)

const admin_act2 = ea.AddSubChannels { channels: subchannel_ids }

// add subchannels, advance phase
const admin_s2 = AdminChannelState {
  ..admin_s1,
  subchannels: subchannel_ids,
  phase: ep.ElectionConfigPhase(ep.ConfigCeremonyPhase),
  seq: admin_s1.seq + 1
}

const admin_tx2_out0 = mock.script_output(
  channel_id(@"admin"),
  mock.admin_datum(admin_s2)
)

fn sub_s0(subchannel_id: ChannelId) -> SubChannelState {
  SubChannelState {
    channel_id: subchannel_id,
    publisher: mock.vkh(subchannel_id),
    new_records: [],
    seq: 0,
  }
}

// Separate variables because we'll want to refer to them in their subchannel sections
const guardian1_s0 = sub_s0(channel_id(@"guardian1"))
const guardian2_s0 = sub_s0(channel_id(@"guardian2"))
const guardian3_s0 = sub_s0(channel_id(@"guardian3"))
const device1_s0   = sub_s0(channel_id(@"device1"  ))
const verifier1_s0 = sub_s0(channel_id(@"verifier1"))

fn sub_output(sub_id: ChannelId, sub_state: SubChannelState) -> Output {
  mock.script_output(sub_id, mock.subchannel_datum(sub_state))
}

// These are outputs of admin_tx2, but could also be called tx0 for their subchannel
const guardian1_tx0_out0 = sub_output(channel_id(@"guardian1"), guardian1_s0)
const guardian2_tx0_out0 = sub_output(channel_id(@"guardian2"), guardian2_s0)
const guardian3_tx0_out0 = sub_output(channel_id(@"guardian3"), guardian3_s0)
const device1_tx0_out0   = sub_output(channel_id(@"device1"  ), device1_s0  )
const verifier1_tx0_out0 = sub_output(channel_id(@"verifier1"), verifier1_s0)

const admin_tx2_subchannel_outputs = [
  guardian1_tx0_out0,
  guardian2_tx0_out0,
  guardian3_tx0_out0,
  device1_tx0_out0,
  verifier1_tx0_out0,
]

const admin_tx2 = Transaction {
  ..transaction.placeholder,
  inputs: [admin_tx2_in0],
  mint: mock.mint_stts(subchannel_ids),
  outputs: [
    admin_tx2_out0,
    ..admin_tx2_subchannel_outputs
 ],
  extra_signatories: [mock.admin_vkh],
}

test happy_election_admin_tx2() {
  mock.election_validate(admin_tx2, admin_act2)
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
