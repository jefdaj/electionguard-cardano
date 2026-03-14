// Happy path through a full election, posting statically generated CIDs.
// This one has enough going on that I need variable naming conventions:
//
// 1. first channel name: admin, guardian1, ...
// 2. then txN where N == seq: 0, 1, ...
// 3. type: (s)tate, (in)put, (out)put, ...
// 4. finally an input/output index: 0, 1, ...
//
// Examples:
// - admin_tx0
// - admin_s0
// - device1_tx3_in0
// - device1_tx3_out0
//
// Tests will be named by channel and txN. Examples:
// - happy_election_admin_tx0
// - happy_election_device1_tx3
//

use cardano/assets
use cardano/transaction.{NoDatum, Transaction, Input, Output}
use election/types/action as ea
use election/types/phase as ep
use election/types/state.{
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

// Automate simple admin transactions that take one input, post some new
// records, and produce one output. Returns the Input too for use in other tests.
fn happy_admin_post(
  input: Input,
  state: AdminChannelState
) -> (Output, Transaction, Input) {
  let output = mock.script_output(a, mock.admin_datum(state))
  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [input],
    outputs: [output],
    extra_signatories: [mock.admin_vkh],
  }
  (output, tx, input)
}

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
  extra_signatories: [mock.admin_vkh],
}

pub fn test_admin_tx0() {
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

pub fn admin_tx1_triple() -> (Output, Transaction, Input) {
  happy_admin_post(
    mock.input(@"admin_tx0", 0, admin_tx0_out0),
    admin_s1
  )
}

pub fn test_admin_tx1() {
  let (_, tx, _) = admin_tx1_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- admin_tx2 -----------

const admin_tx1_out0 = mock.script_output(a, mock.admin_datum(admin_s1))

// TODO is it confusing that you hash the prev tx number here?
pub const admin_tx2_in0 = mock.input(@"admin_tx1", 0, admin_tx1_out0)

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
pub const admin_tx3_in0     = mock.input(@"admin_tx2", 0, admin_tx2_out0    )
pub const guardian1_tx1_in0 = mock.input(@"admin_tx2", 1, guardian1_tx0_out0)
pub const guardian2_tx1_in0 = mock.input(@"admin_tx2", 2, guardian2_tx0_out0)
pub const guardian3_tx1_in0 = mock.input(@"admin_tx2", 3, guardian3_tx0_out0)
pub const device1_tx1_in0   = mock.input(@"admin_tx2", 4, device1_tx0_out0  )
pub const verifier1_tx1_in0 = mock.input(@"admin_tx2", 5, verifier1_tx0_out0)

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

pub fn test_admin_tx2() {
  mock.election_validate(admin_tx2, admin_act2)
}

// =================================
// parallel admin section:
// 3. finalize config
// 4. advance voting -> tally
// 5. results tally
// 6. results decrypt
// 7. verify
// =================================

// ----------- admin_tx3 -----------

// finalize election config, advance to voting
// TODO any issue skipping ConfigFinalizePhase here?
const admin_s3 = AdminChannelState {
  ..admin_s2,
  new_records: [
    sr.joint_key,
    sr.constants,
  ],
  phase: ep.ElectionVotingPhase,
  seq: 3,
}

// admin_tx3_in0 defined above in admin_tx2 section
pub fn admin_tx3_triple() -> (Output, Transaction, Input) {
  happy_admin_post(admin_tx3_in0, admin_s3)
}

pub fn test_admin_tx3() {
  let (_, tx, _) = admin_tx3_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- admin_tx4 -----------

// This could be combined with posting the tally, but in later versions I think
// it would make more sense to have this be a definite stopping point where
// devices post any last votes and their STTs are burned (channels removed). So
// for now I'll keep it as an advance-only step.

const admin_s4 = AdminChannelState {
  ..admin_s3,
  new_records: [],
  phase: ep.ElectionResultsPhase(ep.ResultsTallyPhase),
  seq: 4,
}

pub fn admin_tx4_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = admin_tx3_triple()
  happy_admin_post(
    mock.input(@"admin_tx3", 0, output),
    admin_s4
  )
}

pub fn test_admin_tx4() {
  let (_, tx, _) = admin_tx4_triple()
  mock.election_validate(tx, ea.AdvancePhase)
}

// ----------- admin_tx5 -----------

// post ciphertext tally, advance phase
const admin_s5 = AdminChannelState {
  ..admin_s4,
  new_records: [
    sr.ciphertext_tally,
  ],
  phase: ep.ElectionResultsPhase(ep.ResultsDecryptPhase),
  seq: 5,
}

pub fn admin_tx5_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = admin_tx4_triple()
  happy_admin_post(
    mock.input(@"admin_tx4", 0, output),
    admin_s5
  )
}

pub fn test_admin_tx5() {
  let (_, tx, _) = admin_tx5_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- admin_tx6 -----------

// post plaintext results, advance phase
const admin_s6 = AdminChannelState {
  ..admin_s5,
  new_records: [
    sr.plaintext_tally,
    sr.spoiled_result_476d9db6,
    sr.spoiled_result_480eed2e,
    sr.spoiled_result_48b5dc74,
    sr.spoiled_result_49fb726a,
    sr.spoiled_result_4aa15ab8,
    sr.spoiled_result_4c9f842a,
  ],
  phase: ep.ElectionVerifyPhase,
  seq: 6,
}

pub fn admin_tx6_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = admin_tx5_triple()
  happy_admin_post(
    mock.input(@"admin_tx5", 0, output),
    admin_s6
  )
}

pub fn test_admin_tx6() {
  let (_, tx, _) = admin_tx6_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- admin_tx7 -----------

// post summary
// TODO better to keep separate from advancing phase?
const admin_s7 = AdminChannelState {
  ..admin_s6,
  new_records: [
    sr.admin1_summary, // TODO remove the 1?
  ],
  phase: ep.ElectionFinalizePhase,
  seq: 7,
}

pub fn admin_tx7_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = admin_tx6_triple()
  happy_admin_post(
    mock.input(@"admin_tx6", 0, output),
    admin_s7
  )
}

pub fn test_admin_tx7() {
  let (_, tx, _) = admin_tx7_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// guardian1 transactions:
// 1. key ceremony round 1
// 2. key ceremony round 2
// 3. key ceremony round 3
// 4. decrypt results
// 5. summary (verification)
// =================================

// Automate simple subchannel transactions that take one input, post some new
// records, and produce one output.
fn happy_subchannel_post(
  channel: ChannelId,
  input: Input,
  state: SubChannelState
) -> (Output, Transaction, Input) {
  let output = mock.script_output(channel, mock.subchannel_datum(state))
  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [input],
    outputs: [output],
    extra_signatories: [mock.vkh(channel)],
  }
  (output, tx, input)
}

// ----------- guardian1_tx1 -----------

// key ceremony round 1
const guardian1_s1 = SubChannelState {
  ..guardian1_s0,
  new_records: [
    sr.guardian1_pubkey,
  ],
  seq: 1,
}

// guardian1_tx1_in0 defined above in admin_tx2 section
pub fn guardian1_tx1_triple() -> (Output, Transaction, Input) {
  happy_subchannel_post(g1, guardian1_tx1_in0, guardian1_s1)
}

pub fn test_guardian1_tx1() {
  let (_, tx, _) = guardian1_tx1_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian1_tx2 -----------

// key ceremony round 2
const guardian1_s2 = SubChannelState {
  ..guardian1_s1,
  new_records: [
    sr.guardian1_backup2,
    sr.guardian1_backup3,
  ],
  seq: 2,
}

pub fn guardian1_tx2_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian1_tx1_triple()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx1", 0, output),
    guardian1_s2
  )
}

pub fn test_guardian1_tx2() {
  let (_, tx, _) = guardian1_tx2_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian1_tx3 -----------

// key ceremony round 3
const guardian1_s3 = SubChannelState {
  ..guardian1_s2,
  new_records: [
    sr.guardian1_verification2,
    sr.guardian1_verification3,
  ],
  seq: 3,
}

pub fn guardian1_tx3_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian1_tx2_triple()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx2", 0, output),
    guardian1_s3
  )
}

pub fn test_guardian1_tx3() {
  let (_, tx, _) = guardian1_tx3_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian1_tx4 -----------

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

pub fn guardian1_tx4_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian1_tx3_triple()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx3", 0, output),
    guardian1_s4
  )
}

pub fn test_guardian1_tx4() {
  let (_, tx, _) = guardian1_tx4_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian1_tx5 -----------

// post summary
const guardian1_s5 = SubChannelState {
  ..guardian1_s4,
  new_records: [
    sr.guardian1_summary
  ],
  seq: 5,
}

pub fn guardian1_tx5_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian1_tx4_triple()
  happy_subchannel_post(
    g1,
    mock.input(@"guardian1_tx4", 0, output),
    guardian1_s5
  )
}

pub fn test_guardian1_tx5() {
  let (_, tx, _) = guardian1_tx5_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// guardian2 transactions:
// 1. key ceremony round 1
// 2. key ceremony round 2
// 3. key ceremony round 3
// 4. decrypt results
// 5. summary (verification)
// =================================

// ----------- guardian2_tx1 -----------

// key ceremony round 1
const guardian2_s1 = SubChannelState {
  ..guardian2_s0,
  new_records: [
    sr.guardian2_pubkey,
  ],
  seq: 1,
}

// guardian2_tx1_in0 defined above in admin_tx2 section
pub fn guardian2_tx1_triple() -> (Output, Transaction, Input) {
  happy_subchannel_post(g2, guardian2_tx1_in0, guardian2_s1)
}

pub fn test_guardian2_tx1() {
  let (_, tx, _) = guardian2_tx1_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian2_tx2 -----------

// key ceremony round 2
const guardian2_s2 = SubChannelState {
  ..guardian2_s1,
  new_records: [
    sr.guardian2_backup1,
    sr.guardian2_backup3,
  ],
  seq: 2,
}

pub fn guardian2_tx2_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian2_tx1_triple()
  happy_subchannel_post(
    g2,
    mock.input(@"guardian2_tx1", 0, output),
    guardian2_s2
  )
}

pub fn test_guardian2_tx2() {
  let (_, tx, _) = guardian2_tx2_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian2_tx3 -----------

// key ceremony round 3
const guardian2_s3 = SubChannelState {
  ..guardian2_s2,
  new_records: [
    sr.guardian2_verification1,
    sr.guardian2_verification3,
  ],
  seq: 3,
}

pub fn guardian2_tx3_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian2_tx2_triple()
  happy_subchannel_post(
    g2,
    mock.input(@"guardian2_tx2", 0, output),
    guardian2_s3
  )
}

pub fn test_guardian2_tx3() {
  let (_, tx, _) = guardian2_tx3_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian2_tx4 -----------

// decrypt results
const guardian2_s4 = SubChannelState {
  ..guardian2_s3,
  new_records: [
    sr.guardian2_tally_share,
    sr.guardian2_spoiled_share_476d9db6,
    sr.guardian2_spoiled_share_480eed2e,
    sr.guardian2_spoiled_share_48b5dc74,
    sr.guardian2_spoiled_share_49fb726a,
    sr.guardian2_spoiled_share_4aa15ab8,
    sr.guardian2_spoiled_share_4c9f842a,
  ],
  seq: 4,
}

pub fn guardian2_tx4_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian2_tx3_triple()
  happy_subchannel_post(
    g2,
    mock.input(@"guardian2_tx3", 0, output),
    guardian2_s4
  )
}

pub fn test_guardian2_tx4() {
  let (_, tx, _) = guardian2_tx4_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian2_tx5 -----------

// post summary
const guardian2_s5 = SubChannelState {
  ..guardian2_s4,
  new_records: [
    sr.guardian2_summary
  ],
  seq: 5,
}

pub fn guardian2_tx5_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian2_tx4_triple()
  happy_subchannel_post(
    g2,
    mock.input(@"guardian2_tx4", 0, output),
    guardian2_s5
  )
}

pub fn test_guardian2_tx5() {
  let (_, tx, _) = guardian2_tx5_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// guardian3 transactions:
// 1. key ceremony round 1
// 2. key ceremony round 2
// 3. key ceremony round 3
// 4. decrypt results
// 5. summary (verification)
// =================================

// ----------- guardian3_tx1 -----------

// key ceremony round 1
const guardian3_s1 = SubChannelState {
  ..guardian3_s0,
  new_records: [
    sr.guardian3_pubkey,
  ],
  seq: 1,
}

// guardian3_tx1_in0 defined above in admin_tx2 section
pub fn guardian3_tx1_triple() -> (Output, Transaction, Input) {
  happy_subchannel_post(g3, guardian3_tx1_in0, guardian3_s1)
}

pub fn test_guardian3_tx1() {
  let (_, tx, _) = guardian3_tx1_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian3_tx2 -----------

// key ceremony round 2
const guardian3_s2 = SubChannelState {
  ..guardian3_s1,
  new_records: [
    sr.guardian3_backup1,
    sr.guardian3_backup2,
  ],
  seq: 2,
}

pub fn guardian3_tx2_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian3_tx1_triple()
  happy_subchannel_post(
    g3,
    mock.input(@"guardian3_tx1", 0, output),
    guardian3_s2
  )
}

pub fn test_guardian3_tx2() {
  let (_, tx, _) = guardian3_tx2_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian3_tx3 -----------

// key ceremony round 3
const guardian3_s3 = SubChannelState {
  ..guardian3_s2,
  new_records: [
    sr.guardian3_verification1,
    sr.guardian3_verification2,
  ],
  seq: 3,
}

pub fn guardian3_tx3_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian3_tx2_triple()
  happy_subchannel_post(
    g3,
    mock.input(@"guardian3_tx2", 0, output),
    guardian3_s3
  )
}

pub fn test_guardian3_tx3() {
  let (_, tx, _) = guardian3_tx3_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian3_tx4 -----------

// decrypt results
const guardian3_s4 = SubChannelState {
  ..guardian3_s3,
  new_records: [
    sr.guardian3_tally_share,
    sr.guardian3_spoiled_share_476d9db6,
    sr.guardian3_spoiled_share_480eed2e,
    sr.guardian3_spoiled_share_48b5dc74,
    sr.guardian3_spoiled_share_49fb726a,
    sr.guardian3_spoiled_share_4aa15ab8,
    sr.guardian3_spoiled_share_4c9f842a,
  ],
  seq: 4,
}

pub fn guardian3_tx4_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian3_tx3_triple()
  happy_subchannel_post(
    g3,
    mock.input(@"guardian3_tx3", 0, output),
    guardian3_s4
  )
}

pub fn test_guardian3_tx4() {
  let (_, tx, _) = guardian3_tx4_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- guardian3_tx5 -----------

// post summary
const guardian3_s5 = SubChannelState {
  ..guardian3_s4,
  new_records: [
    sr.guardian3_summary
  ],
  seq: 5,
}

pub fn guardian3_tx5_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = guardian3_tx4_triple()
  happy_subchannel_post(
    g3,
    mock.input(@"guardian3_tx4", 0, output),
    guardian3_s5
  )
}

pub fn test_guardian3_tx5() {
  let (_, tx, _) = guardian3_tx5_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// device1 transactions:
// 1. announce device1
// 2. submit all ballots
// 3. cast/spoil all ballots
// =================================

// ----------- device1_tx1 -----------

const device1_s1 = SubChannelState {
  channel_id: d1,
  publisher: mock.vkh(d1),
  new_records: [
    sr.device1,
  ],
  seq: 1,
}

// device1_tx1_in0 defined above in admin_tx2 section
pub fn device1_tx1_triple() -> (Output, Transaction, Input) {
  happy_subchannel_post(d1, device1_tx1_in0, device1_s1)
}

pub fn test_device1_tx1() {
  let (_, tx, _) = device1_tx1_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- device1_tx2 -----------

// submit all ballots
const device1_s2 = SubChannelState {
  channel_id: d1,
  publisher: mock.vkh(d1),
  new_records: [
    sr.ballot_submitted_476d9db6,
    sr.ballot_submitted_480eed2e,
    sr.ballot_submitted_48b5dc74,
    sr.ballot_submitted_4957f5fe,
    sr.ballot_submitted_49fb726a,
    sr.ballot_submitted_4aa15ab8,
    sr.ballot_submitted_4b4fb8a6,
    sr.ballot_submitted_4bf9df52,
    sr.ballot_submitted_4c9f842a,
    sr.ballot_submitted_4d471122,
    sr.ballot_submitted_4decea16,
    sr.ballot_submitted_4e970104,
  ],
  seq: 2,
}

pub fn device1_tx2_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = device1_tx1_triple()
  happy_subchannel_post(
    d1,
    mock.input(@"device1_tx1", 0, output),
    device1_s2
  )
}

pub fn test_device1_tx2() {
  let (_, tx, _) = device1_tx2_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// ----------- device1_tx3 -----------

// cast/spoil all ballots
const device1_s3 = SubChannelState {
  channel_id: d1,
  publisher: mock.vkh(d1),
  new_records: [
    sr.ballot_spoiled_476d9db6,
    sr.ballot_spoiled_480eed2e,
    sr.ballot_spoiled_48b5dc74,
    sr.ballot_spoiled_49fb726a,
    sr.ballot_spoiled_4aa15ab8,
    sr.ballot_spoiled_4c9f842a,
    sr.cast_notice_4957f5fe,
    sr.cast_notice_4b4fb8a6,
    sr.cast_notice_4bf9df52,
    sr.cast_notice_4d471122,
    sr.cast_notice_4decea16,
    sr.cast_notice_4e970104,
  ],
  seq: 3,
}

pub fn device1_tx3_triple() -> (Output, Transaction, Input) {
  let (output, _, _) = device1_tx2_triple()
  happy_subchannel_post(
    d1,
    mock.input(@"device1_tx2", 0, output),
    device1_s3
  )
}

pub fn test_device1_tx3() {
  let (_, tx, _) = device1_tx3_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// verifier1 transactions:
// 1. post summary (verification)
// =================================

// post verification, advance phase
const verifier1_s1 = SubChannelState {
  channel_id: v1,
  publisher: mock.vkh(v1),
  new_records: [
    sr.verifier1_summary,
  ],
  seq: 1,
}

// verifier1_tx1_in0 defined above in admin_tx2 section
pub fn verifier1_tx1_triple() -> (Output, Transaction, Input) {
  happy_subchannel_post(v1, verifier1_tx1_in0, verifier1_s1)
}

pub fn test_verifier1_tx1() {
  let (_, tx, _) = verifier1_tx1_triple()
  mock.election_validate(tx, ea.PostPublicRecords)
}

// =================================
// final admin section:
// 8. rm subchannels
// 9. end election
// =================================

// ----------- admin_tx8 -----------

const admin_act8 = ea.RmSubChannels { channels: subchannel_ids }

fn admin_tx8_inputs() -> List<Input> {
  let (a_out , _, _) = admin_tx7_triple()
  let (g1_out, _, _) = guardian1_tx5_triple()
  let (g2_out, _, _) = guardian2_tx5_triple()
  let (g3_out, _, _) = guardian3_tx5_triple()
  let (d1_out, _, _) = device1_tx1_triple()
  let (v1_out, _, _) = verifier1_tx1_triple()

  // Each of these is output 0 from a different transaction.
  let in0 = mock.input(@"admin_tx7"    , 0, a_out )
  let in1 = mock.input(@"guardian1_tx5", 0, g1_out)
  let in2 = mock.input(@"guardian2_tx5", 0, g2_out)
  let in3 = mock.input(@"guardian3_tx5", 0, g3_out)
  let in4 = mock.input(@"device1_tx3"  , 0, d1_out)
  let in5 = mock.input(@"verifier1_tx1", 0, v1_out)

  [in0, in1, in2, in3, in4, in5]
}

// remove subchannels
const admin_s8 = AdminChannelState {
  ..admin_s7,
  subchannels: [],
  new_records: [],
  seq: 8,
}

const admin_tx8_out0 = mock.script_output(a, mock.admin_datum(admin_s8))

const admin_tx8 = Transaction {
  ..transaction.placeholder,
  inputs: admin_tx8_inputs(),
  mint: mock.burn_stts(subchannel_ids),
  outputs: [admin_tx8_out0],
  extra_signatories: [mock.admin_vkh],
}

pub fn test_admin_tx8() {
  mock.election_validate(admin_tx8, admin_act8)
}

// ----------- admin_tx9 -----------

const admin_tx9_out0 = Output {
  address: mock.admin_address(), // admin's personal wallet
  value: assets.zero, // TODO ADA here?
  datum: NoDatum,
  reference_script: None,
}

const admin_tx9 = Transaction {
  ..transaction.placeholder,
  mint: mock.burn_stt("admin"),
  inputs: [mock.input(@"admin_tx8", 0, admin_tx8_out0)],
  outputs: [admin_tx9_out0],
  extra_signatories: [mock.admin_vkh],
}

pub fn test_admin_tx9() {
  mock.election_validate(admin_tx9, ea.EndElection)
}
