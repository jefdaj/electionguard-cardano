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
use cardano/transaction.{Transaction, Input, Output}
use election/action as ea
use election/phase as ep
use election/state.{
  ChannelId, channel_id,
  AdminChannelState, SubChannelState
}
use tests/data/static_election_records as sr
use tests/mock

// =================================
// shorthand
// =================================

const a  = channel_id(@"admin")
const g1 = channel_id(@"guardian1")
const g2 = channel_id(@"guardian2")
const g3 = channel_id(@"guardian3")
const d1 = channel_id(@"device1")
const v1 = channel_id(@"verifier1")

const subchannel_ids: List<ChannelId> = [g1, g2, g3, d1, v1]

// =================================
// initial solo admin transactions:
// 0. init election
// 1. announce config
// 2. onboarding (add subchannels)
// =================================

// ----------- admin_tx0 -----------

const admin_s0 = AdminChannelState {
  admin: mock.admin_vkh,
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigAnnouncePhase),
  seq: 0
}

const admin_tx0_out0 = mock.script_output(a, mock.admin_datum(admin_s0))

const admin_tx0 = Transaction {
  ..transaction.placeholder,
  mint: mock.stt_value(a),
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

const admin_tx1_out0 = mock.script_output(a, mock.admin_datum(admin_s1))

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

// TODO is it confusing that you hash the prev tx number here?
const admin_tx2_in0 = mock.input(@"admin_tx1", 0, admin_tx1_out0)

const admin_act2 = ea.AddSubChannels { channels: subchannel_ids }

// add subchannels, advance phase
const admin_s2 = AdminChannelState {
  admin: mock.admin_vkh,
  new_records: [],
  subchannels: subchannel_ids,
  phase: ep.ElectionConfigPhase(ep.ConfigCeremonyPhase),
  seq: admin_s1.seq + 1
}

const admin_tx2_out0 = mock.script_output(a, mock.admin_datum(admin_s2))

fn sub_s0(subchannel_id: ChannelId) -> SubChannelState {
  SubChannelState {
    channel_id: subchannel_id,
    publisher: mock.vkh(subchannel_id),
    new_records: [],
    seq: 0,
  }
}

// We'll want to refer to these in their subchannel sections.
const guardian1_s0 = sub_s0(g1)
const guardian2_s0 = sub_s0(g2)
const guardian3_s0 = sub_s0(g3)
const device1_s0   = sub_s0(d1)
const verifier1_s0 = sub_s0(v1)

fn sub_out0(sub_id: ChannelId, sub_state: SubChannelState) -> Output {
  mock.script_output(sub_id, mock.subchannel_datum(sub_state))
}

// These are outputs of admin_tx2, and also tx0 of their subchannels.
const guardian1_tx0_out0 = sub_out0(g1, guardian1_s0)
const guardian2_tx0_out0 = sub_out0(g2, guardian2_s0)
const guardian3_tx0_out0 = sub_out0(g3, guardian3_s0)
const device1_tx0_out0   = sub_out0(d1, device1_s0  )
const verifier1_tx0_out0 = sub_out0(v1, verifier1_s0)

// And matching inputs. Not used until subchannel sections below, but easier to
// write here where the indexes are obvious.
// const admin_tx3_in0     = mock.input(@"admin_tx2", 0, admin_tx2_out0    )
const guardian1_tx1_in0 = mock.input(@"admin_tx2", 1, guardian1_tx0_out0)
// const guardian2_tx1_in0 = mock.input(@"admin_tx2", 2, guardian2_tx0_out0)
// const guardian3_tx1_in0 = mock.input(@"admin_tx2", 3, guardian3_tx0_out0)
const device1_tx1_in0   = mock.input(@"admin_tx2", 4, device1_tx0_out0  )
const verifier1_tx1_in0 = mock.input(@"admin_tx2", 5, verifier1_tx0_out0)

const admin_tx2 = Transaction {
  ..transaction.placeholder,
  inputs: [admin_tx2_in0],
  mint: mock.mint_stts(subchannel_ids),
  outputs: [
    admin_tx2_out0,
    guardian1_tx0_out0,
    guardian2_tx0_out0,
    guardian3_tx0_out0,
    device1_tx0_out0,
    verifier1_tx0_out0,
 ],
  extra_signatories: [mock.admin_vkh],
}

test happy_election_admin_tx2() {
  mock.election_validate(admin_tx2, admin_act2)
}

// =================================
// parallel admin section:
// 3. ceremony
// 4. finalize config (device here?)
// 5. voting
// 6. results tally
// 7. results decrypt
// 8. verify
// =================================

// =================================
// admin
// =================================

// admin_tx3

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
// guardian1 transactions:
// 1. key ceremony round 1
// 2. key ceremony round 2
// 3. key ceremony round 3
// 4. decrypt results
// 5. summary (verification)
// =================================

// TODO later, can 4 and 5 be done together?

// Automate simple subchannel posts with one input and one output
fn happy_subchannel_post(
  channel: ChannelId,
  input: Input,
  state: SubChannelState
) -> (Output, Transaction) {
  let output = mock.script_output(channel, mock.subchannel_datum(state))
  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [input],
    outputs: [output],
    extra_signatories: [mock.vkh(channel)],
  }
  (output, tx)
}

// key ceremony round 1
const guardian1_s1 = SubChannelState {
  ..guardian1_s0,
  new_records: [
    sr.guardian1_pubkey,
  ],
  seq: 1,
}

// guardian1_tx1_in0 defined above in admin_tx2 section
fn guardian1_tx1_pair() -> (Output, Transaction) {
  happy_subchannel_post(g1, guardian1_tx1_in0, guardian1_s1)
}

test happy_election_guardian1_tx1() {
  let (_, tx) = guardian1_tx1_pair()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// key ceremony round 2
const guardian1_s2 = SubChannelState {
  ..guardian1_s1,
  new_records: [
    sr.guardian1_backup2,
    sr.guardian1_backup3,
  ],
  seq: 2,
}

fn guardian1_tx2_pair() -> (Output, Transaction) {
  let (output, _) = guardian1_tx1_pair()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx1", 0, output),
    guardian1_s2
  )
}

test happy_election_guardian1_tx2() {
  let (_, tx) = guardian1_tx2_pair()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// key ceremony round 3
const guardian1_s3 = SubChannelState {
  ..guardian1_s2,
  new_records: [
    sr.guardian1_verification2,
    sr.guardian1_verification3,
  ],
  seq: 3,
}

fn guardian1_tx3_pair() -> (Output, Transaction) {
  let (output, _) = guardian1_tx2_pair()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx2", 0, output),
    guardian1_s3
  )
}

test happy_election_guardian1_tx3() {
  let (_, tx) = guardian1_tx3_pair()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// decrypt results
const guardian1_s4 = SubChannelState {
  ..guardian1_s3,
  new_records: [
    sr.guardian1_tally_share,
    sr.guardian1_spoiled_share_476d9db6,
    sr.guardian1_spoiled_share_480eed2e,
    sr.guardian1_spoiled_share_48b5dc74,
    sr.guardian1_spoiled_share_49fb726a,
    sr.guardian1_spoiled_share_4aa15ab8,
    sr.guardian1_spoiled_share_4c9f842a,
  ],
  seq: 4,
}

fn guardian1_tx4_pair() -> (Output, Transaction) {
  let (output, _) = guardian1_tx3_pair()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx3", 0, output),
    guardian1_s4
  )
}

test happy_election_guardian1_tx4() {
  let (_, tx) = guardian1_tx4_pair()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// TODO duplicate for guardian2, guardian3

// =================================
// device1 transactions:
// 1. announce device1
// 2. ...
// =================================

const device1_s1 = SubChannelState {
  channel_id: d1,
  publisher: mock.vkh(d1),
  new_records: [
    sr.device1,
  ],
  seq: 1,
}

// device1_tx1_in0 defined above in admin_tx2 section
fn device1_tx1_pair() -> (Output, Transaction) {
  happy_subchannel_post(d1, device1_tx1_in0, device1_s1)
}

test happy_election_device1_tx1() {
  let (_, tx) = device1_tx1_pair()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// verifier1 transactions:
// 1. post summary (verification)
// =================================

const verifier1_s1 = SubChannelState {
  channel_id: v1,
  publisher: mock.vkh(v1),
  new_records: [
    sr.verifier1_summary,
  ],
  seq: 1,
}

// verifier1_tx1_in0 defined above in admin_tx2 section
fn verifier1_tx1_pair() -> (Output, Transaction) {
  happy_subchannel_post(v1, verifier1_tx1_in0, verifier1_s1)
}

test happy_election_verifier1_tx1() {
  let (_, tx) = verifier1_tx1_pair()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// final solo admin section:
// 1. rm subchannels
// 2. end election
// =================================
