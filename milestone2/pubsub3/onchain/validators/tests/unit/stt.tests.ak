use cardano/address.{Address, Script}
use cardano/assets
use cardano/transaction.{InlineDatum, Input, Output, OutputReference, Transaction}

use election/record as r
use election/state as s

use election/stt

test tx_sends_token_to_addr_valid() {
  // Setup: Mock data
  let policy_id = #"aabbccdd"
  let stt_name = "egc-election-testchannel1"
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

  let found_output = stt.tx_sends_token_to_addr(tx, policy_id, stt_name, script_address, 1)
  found_output == Some(stt_output)
}
