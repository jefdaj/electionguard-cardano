use cardano/assets.{Value}
use cardano/transaction.{Input, Datum, InlineDatum, NoDatum, Output, Transaction}
use election/action.{InitElection}
use election/phase.{ElectionConfigPhase, ConfigAnnouncePhase}
use election/state.{ChannelState, AdminChannel, AdminChannelState}
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

fn oneshot_value() -> Value {
  assets.from_asset(
    policy_id: mock.policy_id(),
    asset_name: stt.full_stt_name("admin"),
    quantity: 1
  )
}

fn output0() -> Output {
  Output {
    address: mock.script_address(),
    value: oneshot_value(),
    datum: datum0(),
    reference_script: None,
  }
}

fn tx0() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    mint: oneshot_value(),
    extra_signatories: [],
    inputs: [oneshot_input()],
    outputs: [output0()],
  }
}

test test_minimal_initelection() {
  mock.election_validate(tx0(), InitElection)
}
