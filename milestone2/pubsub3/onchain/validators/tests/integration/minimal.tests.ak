// based on test_simple_oneshot from the aiken src code

// use aiken/collection/list
// use cardano/address.{Address, VerificationKey}
use cardano/assets
use cardano/transaction.{Input, NoDatum, Output, Transaction}

// pub const own_hash = #"dead"
// pub const other_hash = #"c0ffee"
// pub const beneficiary_keyhash = #"c001"

// validator simple_oneshot(utxo_ref: OutputReference) {
//   mint(_r: Void, _policy_id: ByteArray, self: Transaction) {
//     let Transaction { inputs, .. } = self
//     when list.find(inputs, fn(input) { input.output_reference == utxo_ref }) is {
//       Some(_) -> True
//       None -> False
//     }
//   }
//   // TODO is this needed in current aiken?
//   else(_) {
//     fail
//   }
// }

use tests/mock

use election/action.{InitElection}
use election/stt

test test_wip_initelection() {
  // TODO conditions checked by mint():
  // - has oneshot utxo ref as an input
  // - mints exactly one token: "egc-election-admin-channel-state"
  // TODO conditions checked by spend():
  // - datum is None (is that different from NoDatum?)
  // - get_continuation_state finds cont_state
  // - new_records empty
  // - subchannels empty
  // - seq == 0
  // - phase is ElectionConfigPhase(ConfigAnnouncePhase)

  let redeemer = InitElection

  let own_hash = mock.policy_id()

  let oneshot_utxo = mock.oneshot_oref()

  // The output used to 
  // TODO move -> mock.oneshot_output?
  let output0 =
    Output {
      address: mock.admin_address(),
      value: assets.zero,
      datum: NoDatum, // TODO start admin stt here
      reference_script: None,
    }

  // TODO move -> mock.oneshot_input?
  let oneshot_input = Input {
    output_reference: oneshot_utxo,
    output: output0
  }

  let output1 =
    Output {
      address: mock.script_address(),
      value: assets.zero,
      datum: NoDatum, // TODO start admin stt here
      reference_script: None,
    }

  let stt_name = stt.full_stt_name("admin")
  let mint = assets.from_asset(
    policy_id: own_hash,
    asset_name: stt_name,
    quantity: 1
  )

  let tx =
    Transaction {
      ..transaction.placeholder,
      mint: mint,
      extra_signatories: [],
      inputs: [oneshot_input],
      outputs: [output1],
    }

  // simple_oneshot.mint(utxo, Void, own_hash, tx) == True
  mock.election_validate(tx, redeemer)
}
