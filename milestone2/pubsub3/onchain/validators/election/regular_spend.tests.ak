use cardano/address.{Address, Script}
use cardano/assets
use cardano/transaction.{InlineDatum, Input, Output, OutputReference, Transaction}

use election
use election/action as a
use election/record as r
use election/state as s

test post_to_subchannel_valid() {
  // Setup: Mock data
  let policy_id = #"aabbccdd"
  let stt_name = #"cafe"
  let publisher_vkh = #"abc123"
  let channel_id = #"c001"

  let script_address = Address {
    payment_credential: Script(policy_id),
    stake_credential: None,
  }

  // Old state: subchannel with seq=5, empty new_records
  let old_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: [],
    seq: 5,
  })

  // New records being posted
  // TODO make them realistic for a PostPublicRecord tx
  // TODO records fuzzer?
  let new_records = [
    r.PublicRecord { cid: #"deadbeef", metadata: r.Manifest },
    r.PublicRecord { cid: #"baadf00d", metadata: r.CeremonyDetails },
  ]

  // Expected new state: seq incremented, new_records updated
  let new_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: new_records,
    seq: 6,
  })

  // Build input UTxO (the subchannel being spent)
  let own_ref = OutputReference {
    transaction_id: #"fade00",
    output_index: 0,
  }

  let own_input = Input {
    output_reference: own_ref,
    output: Output {
      address: script_address,
      value: assets.from_lovelace(2_000_000)
        |> assets.add(policy_id, stt_name, 1),
      datum: InlineDatum(old_state),
      reference_script: None,
    },
  }

  // Build output UTxO (the continued subchannel)
  let stt_output = Output {
    address: script_address,
    value: assets.from_lovelace(2_000_000)
      |> assets.add(policy_id, stt_name, 1),
    datum: InlineDatum(new_state),
    reference_script: None,
  }

  // Build transaction context
  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [own_input],
    outputs: [stt_output],
    fee: 200_000,
    extra_signatories: [publisher_vkh],
    id: #"c0ffee",
  }

  // Execute validator logic
  let redeemer = a.RegularAct(a.PostPublicRecords)

  let oneshot_ref = OutputReference {
    transaction_id: #"dead",
    output_index: 0,
  }

  // This should pass
  election.election.spend(
    oneshot_ref, // TODO is this really where validator params are supposed to go?
    Some(old_state),
    redeemer,
    own_ref,
    tx,
  )
}

test post_to_subchannel_wrong_publisher_fails() {
  let policy_id = #"aabbccdd"
  let stt_name = #"cafe"
  let publisher_vkh = #"abc123"
  let wrong_vkh = #"bad999"
  let channel_id = #"c001"

  let script_address = Address {
    payment_credential: Script(policy_id),
    stake_credential: None,
  }

  let old_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: [],
    seq: 5,
  })

  let new_records = [
    r.PublicRecord { cid: #"deadbeef", metadata: r.Manifest },
  ]

  let new_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: new_records,
    seq: 6,
  })

  let own_ref = OutputReference {
    transaction_id: #"fade00",
    output_index: 0,
  }

  let own_input = Input {
    output_reference: own_ref,
    output: Output {
      address: script_address,
      value: assets.from_lovelace(2_000_000)
        |> assets.add(policy_id, stt_name, 1),
      datum: InlineDatum(old_state),
      reference_script: None,
    },
  }

  let stt_output = Output {
    address: script_address,
    value: assets.from_lovelace(2_000_000)
      |> assets.add(policy_id, stt_name, 1),
    datum: InlineDatum(new_state),
    reference_script: None,
  }

  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [own_input],
    outputs: [stt_output],
    fee: 200_000,
    extra_signatories: [wrong_vkh],
    id: #"c0ffee",
  }

  let redeemer = a.RegularAct(a.PostPublicRecords)

  let oneshot_ref = OutputReference {
    transaction_id: #"dead",
    output_index: 0,
  }

  // This should fail
  !election.election.spend(oneshot_ref, Some(old_state), redeemer, own_ref, tx)
}

test post_to_subchannel_stt_not_continued_fails() {
  let policy_id = #"aabbccdd"
  let stt_name = #"cafe"
  let publisher_vkh = #"abc123"
  let channel_id = #"c001"

  let script_address = Address {
    payment_credential: Script(policy_id),
    stake_credential: None,
  }

  let old_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: [],
    seq: 5,
  })

  let new_records = [
    r.PublicRecord { cid: #"deadbeef", metadata: r.Manifest },
  ]

  let new_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: new_records,
    seq: 6,
  })

  let own_ref = OutputReference {
    transaction_id: #"fade00",
    output_index: 0,
  }

  let own_input = Input {
    output_reference: own_ref,
    output: Output {
      address: script_address,
      value: assets.from_lovelace(2_000_000)
        |> assets.add(policy_id, stt_name, 1),
      datum: InlineDatum(old_state),
      reference_script: None,
    },
  }

  // Output missing the STT!
  let bad_output = Output {
    address: script_address,
    value: assets.from_lovelace(2_000_000),
    datum: InlineDatum(new_state),
    reference_script: None,
  }

  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [own_input],
    outputs: [bad_output],
    fee: 200_000,
    extra_signatories: [publisher_vkh],
    id: #"c0ffee",
  }

  let redeemer = a.RegularAct(a.PostPublicRecords)

  let oneshot_ref = OutputReference {
    transaction_id: #"dead",
    output_index: 0,
  }

  // Should fail because tx_sends_token_to_addr returns None
  !election.election.spend(oneshot_ref, Some(old_state), redeemer, own_ref, tx)
}

test post_to_subchannel_seq_not_incremented_fails() {
  let policy_id = #"aabbccdd"
  let stt_name = #"cafe"
  let publisher_vkh = #"abc123"
  let channel_id = #"c001"

  let script_address = Address {
    payment_credential: Script(policy_id),
    stake_credential: None,
  }

  let old_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: [],
    seq: 5,
  })

  let new_records = [
    r.PublicRecord { cid: #"deadbeef", metadata: r.Manifest },
  ]

  // Wrong: seq should be 6, not 5
  let bad_new_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: new_records,
    seq: 5,
  })

  let own_ref = OutputReference {
    transaction_id: #"fade00",
    output_index: 0,
  }

  let own_input = Input {
    output_reference: own_ref,
    output: Output {
      address: script_address,
      value: assets.from_lovelace(2_000_000)
        |> assets.add(policy_id, stt_name, 1),
      datum: InlineDatum(old_state),
      reference_script: None,
    },
  }

  let stt_output = Output {
    address: script_address,
    value: assets.from_lovelace(2_000_000)
      |> assets.add(policy_id, stt_name, 1),
    datum: InlineDatum(bad_new_state),
    reference_script: None,
  }

  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [own_input],
    outputs: [stt_output],
    fee: 200_000,
    extra_signatories: [publisher_vkh],
    id: #"c0ffee",
  }

  let redeemer = a.RegularAct(a.PostPublicRecords)

  let oneshot_ref = OutputReference {
    transaction_id: #"dead",
    output_index: 0,
  }

  // Should fail: expected_new_state != new_state
  !election.election.spend(oneshot_ref, Some(old_state), redeemer, own_ref, tx)
}

test post_to_subchannel_ada_withdrawn_fails() {
  let policy_id = #"aabbccdd"
  let stt_name = #"cafe"
  let publisher_vkh = #"abc123"
  let channel_id = #"c001"

  let script_address = Address {
    payment_credential: Script(policy_id),
    stake_credential: None,
  }

  let old_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: [],
    seq: 5,
  })

  let new_records = [
    r.PublicRecord { cid: #"deadbeef", metadata: r.Manifest },
  ]

  let new_state = s.SubChannel(s.SubChannelState {
    channel_id: channel_id,
    publisher: publisher_vkh,
    new_records: new_records,
    seq: 6,
  })

  let own_ref = OutputReference {
    transaction_id: #"fade00",
    output_index: 0,
  }

  let own_input = Input {
    output_reference: own_ref,
    output: Output {
      address: script_address,
      value: assets.from_lovelace(2_000_000)
        |> assets.add(policy_id, stt_name, 1),
      datum: InlineDatum(old_state),
      reference_script: None,
    },
  }

  // Output has less ADA - withdrawal attempt!
  let stt_output = Output {
    address: script_address,
    value: assets.from_lovelace(1_500_000)
      |> assets.add(policy_id, stt_name, 1),
    datum: InlineDatum(new_state),
    reference_script: None,
  }

  let tx = Transaction {
    ..transaction.placeholder,
    inputs: [own_input],
    outputs: [stt_output],
    fee: 200_000,
    extra_signatories: [publisher_vkh],
    id: #"c0ffee",
  }

  let redeemer = a.RegularAct(a.PostPublicRecords)

  let oneshot_ref = OutputReference {
    transaction_id: #"dead",
    output_index: 0,
  }

  // Should fail: channel_ada_preserved returns False
  !election.election.spend(oneshot_ref, Some(old_state), redeemer, own_ref, tx)
}
