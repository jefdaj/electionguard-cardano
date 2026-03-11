// Test posting public records from the admin channel or a subchannel.

use aiken/primitive/string
use cardano/transaction.{Input, Output, OutputReference, Transaction}
use election/state.{AdminChannelState, SubChannelState}
use election/action as ea
use election/phase as ep
use election/record as er
use tests/mock

const manifest = er.PublicRecord {
  // orig base32: bafkreiat5mhmsrevctm43qlv6aokrli3cdoj2aqyb34wsf6idybuvzwtua
  cid: #"0155122013eb0ec9449514d9cdc175f01ca8ad1b10dc9d02180ef96917c81e034ae6d3a0",
  metadata: er.Manifest,
}

// ===============================
// post to admin channel
// ===============================

const admin_state0 =  AdminChannelState {
  admin: mock.admin_vkh(),
  subchannels: [],
  new_records: [],
  phase: ep.ElectionConfigPhase(ep.ConfigAnnouncePhase),
  seq: 0
}

const admin_output0 = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_state0),
  reference_script: None,
}

const admin_input = Input {
  output_reference: OutputReference {
    transaction_id: "abc1",
    output_index: 0,
  },
  output: admin_output0,
}

fn admin_state1() -> AdminChannelState {
  AdminChannelState {
    admin: mock.admin_vkh(),
    subchannels: [],
    new_records: [manifest, manifest, manifest], // duplicates, but doesn't matter here
    phase: ep.ElectionConfigPhase(ep.ConfigAnnouncePhase),
    seq: admin_state0.seq + 1,
  }
}

const admin_output1 = Output {
  address: mock.script_address(),
  value: mock.stt_value("admin"),
  datum: mock.admin_datum(admin_state1()),
  reference_script: None,
}

fn admin_tx() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    inputs: [admin_input],
    outputs: [admin_output1],
    extra_signatories: [mock.admin_vkh()],
  }
}

test happy_postpublicrecords_admin() {
  mock.election_validate(admin_tx(), ea.PostPublicRecords)
}

// ===============================
// post to a subchannel
// ===============================

const subchannel_id = string.to_bytearray(@"guardian1")

const sub_state0 =  SubChannelState {
  channel_id: subchannel_id,
  publisher: mock.vkh(subchannel_id),
  new_records: [],
  seq: 0
}

const sub_output0 = Output {
  address: mock.script_address(),
  value: mock.stt_value(subchannel_id),
  datum: mock.subchannel_datum(sub_state0),
  reference_script: None,
}

const sub_input = Input {
  output_reference: OutputReference {
    transaction_id: "abc1",
    output_index: 0,
  },
  output: sub_output0,
}

fn sub_state1() -> SubChannelState {
  SubChannelState {
    channel_id: subchannel_id,
    publisher: mock.vkh(subchannel_id),
    new_records: [manifest], // wrong record type, but doesn't matter here
    seq: sub_state0.seq + 1,
  }
}

const sub_output1 = Output {
  address: mock.script_address(),
  value: mock.stt_value(subchannel_id),
  datum: mock.subchannel_datum(sub_state1()),
  reference_script: None,
}

fn sub_tx() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    inputs: [sub_input],
    outputs: [sub_output1],
    extra_signatories: [mock.vkh(subchannel_id)],
  }
}

test happy_postpublicrecords_subchannel() {
  mock.election_validate(sub_tx(), ea.PostPublicRecords)
}
