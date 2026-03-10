// The first integration test. It'll take the simplest happy path through the
// contract lifecycle, not bothering to post valid election artifacts:
//
// - InitElection
// - AdvancePhase (7X)
// - EndElection
//

use cardano/assets.{Value}
use cardano/transaction.{Input, Datum, InlineDatum, NoDatum, Output, OutputReference, Transaction}
use election/action as ea
use election/phase as ep
use election/state.{AdminChannel, AdminChannelState}
use election/stt
use tests/mock

fn oneshot_output() -> Output {
  Output {
    address: mock.admin_address(), // admin's personal wallet
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

fn state0() -> AdminChannelState {
  AdminChannelState {
    admin: mock.admin_vkh(),
    subchannels: [],
    new_records: [],
    phase: ep.ElectionConfigPhase(ep.ConfigAnnouncePhase),
    seq: 0
  }
}

fn admin_datum(state: AdminChannelState) -> Datum {
  InlineDatum(Some(AdminChannel(state)))
}

fn admin_stt_value() -> Value {
  assets.from_asset(
    policy_id: mock.policy_id(),
    asset_name: stt.full_stt_name("admin"),
    quantity: 1
  )
}

fn output0() -> Output {
  Output {
    address: mock.script_address(),
    value: admin_stt_value(),
    datum: admin_datum(state0()),
    reference_script: None,
  }
}

fn tx0() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    mint: admin_stt_value(),
    // extra_signatories: [],
    inputs: [oneshot_input()],
    outputs: [output0()],
  }
}

// My convention for now is to label transactions by election id/container
// name, then STT seq number. So admin_tx0, admin_tx1, guardian1_tx1, etc.
test test_minimal_admin_tx0_initelection() {
  mock.election_validate(tx0(), ea.InitElection)
}

fn input1() -> Input {
  Input {
    output_reference: OutputReference {
      transaction_id: #"abc1", // TODO figure this out! how should it be created?
      output_index: 0,
    },
    output: output0()
  }
}

fn output1() -> Output {
  Output {
    address: mock.script_address(),
    value: admin_stt_value(),
    datum: admin_datum(state1()),
    reference_script: None,
  }
}

fn state1() -> AdminChannelState {
  AdminChannelState {
    ..state0(),
    phase: ep.ElectionConfigPhase(ep.ConfigOnboardingPhase),
    seq: 1
  }
}

fn tx1() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    inputs: [input1()],
    outputs: [output1()],
    extra_signatories: [mock.admin_vkh()],
  }
}

test test_minimal_admin_tx1_onboarding() {
  mock.election_validate(tx1(), ea.AdvancePhase)
}
