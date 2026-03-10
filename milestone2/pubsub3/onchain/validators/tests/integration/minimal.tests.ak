// based on test_simple_oneshot from the aiken src code

// use aiken/collection/list
// use cardano/address.{Address, VerificationKey}
use cardano/assets.{Value}
use cardano/transaction.{Input, Datum, InlineDatum, NoDatum, Output, Transaction}

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
use election/state.{ChannelState, AdminChannel, AdminChannelState}
use election/phase.{ElectionConfigPhase, ConfigAnnouncePhase}
use election/stt

// This is owned by the admin's regular wallet, not by the script.
fn oneshot_output() -> Output {
  Output {
    address: mock.admin_address(),
    value: assets.zero,
    datum: NoDatum,
    reference_script: None,
  }
}

fn oneshot_input() -> Input {
  Input {
    output_reference: mock.oneshot_oref(),
    output: oneshot_output()
  }
}

fn state0() -> ChannelState {
  AdminChannel(AdminChannelState {
    admin: mock.admin_vkh(),
    subchannels: [],
    new_records: [],
    phase: ElectionConfigPhase(ConfigAnnouncePhase),
    seq: 0
  })
}

fn datum0() -> Datum {
  InlineDatum(Some(state0()))
}

fn output0() -> Output {
  Output {
    address: mock.script_address(), // TODO error here?
    value: assets.zero,
    datum: datum0(),
    reference_script: None,
  }
}

fn oneshot_mint() -> Value {
  assets.from_asset(
    policy_id: mock.policy_id(),
    asset_name: stt.full_stt_name("admin"),
    quantity: 1
  )
}

fn tx0() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    mint: oneshot_mint(),
    extra_signatories: [],
    inputs: [oneshot_input()],
    outputs: [output0()],
  }
}

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
  mock.election_validate(tx0(), InitElection)
}
