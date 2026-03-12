// The first integration test. It'll take the simplest happy path through the
// admin channel lifecycle, not bothering to post valid election artifacts:
//
// - InitElection
// - AdvancePhase (7X)
// - EndElection
//

use aiken/collection/list
use cardano/assets
use cardano/transaction.{Input, NoDatum, Output, Transaction}
use election/action as ea
use election/phase as ep
use election/state.{AdminChannelState}
use tests/mock

// ====================
// InitElection
// ====================

// My convention for now is to label transactions by election id/container
// name, then STT seq number. So admin_tx0, admin_tx1, guardian1_tx1, etc.
test happy_adminchannel_initelection() {
  mock.election_validate(tx0(), ea.InitElection)
}

fn tx0() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    mint: mock.stt_value("admin"),
    inputs: [mock.oneshot_input],
    outputs: [output0()],
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

fn output0() -> Output {
  Output {
    address: mock.script_address(),
    value: mock.stt_value("admin"),
    datum: mock.admin_datum(state0()),
    reference_script: None,
  }
}

// ====================
// AdvancePhase
// ====================

const minimal_states = [
  (1, ep.ElectionConfigPhase(ep.ConfigAnnouncePhase)  ),
  (2, ep.ElectionConfigPhase(ep.ConfigOnboardingPhase)),
  (3, ep.ElectionConfigPhase(ep.ConfigCeremonyPhase)  ),
  (4, ep.ElectionConfigPhase(ep.ConfigFinalizePhase)  ),
  (5, ep.ElectionVotingPhase                          ),
  (6, ep.ElectionResultsPhase(ep.ResultsTallyPhase)   ),
  (7, ep.ElectionResultsPhase(ep.ResultsDecryptPhase) ),
  (8, ep.ElectionVerifyPhase                          ),
  (9, ep.ElectionFinalizePhase                        ),
]

// In these minimal tests state n should have seq n (not generally true),
// and the phase at index n in the minimal_states list.
fn minimal_state(n: Int) -> AdminChannelState {
  expect Some((seq, phase)) = list.at(minimal_states, n-1) // zero indexed
  trace @"seq" : seq
  trace @"phase" : phase
  AdminChannelState {
    ..state0(),
    phase: phase,
    seq: seq,
  }
}

// Output n refers to state n.
fn minimal_output(n: Int) -> Output {
  Output {
    address: mock.script_address(),
    value: mock.stt_value("admin"),
    datum: mock.admin_datum(minimal_state(n)),
    reference_script: None,
  }
}


// Input n refers to output (n-1), which includes the datum for state (n-1).
fn minimal_input(n: Int) -> Input {
  mock.input(@"abcdef", n, minimal_output(n-1))
}

// TX n consumes input n and produces output n.
fn minimal_tx(n: Int) {
  let input  = minimal_input(n)
  let output = minimal_output(n)
  Transaction {
    ..transaction.placeholder,
    inputs: [input],
    outputs: [output],
    extra_signatories: [mock.admin_vkh()],
  }
}

// phase 1 is tested in the InitElection section above
test happy_adminchannel_advancephase_2() { mock.election_validate(minimal_tx(2), ea.AdvancePhase) }
test happy_adminchannel_advancephase_3() { mock.election_validate(minimal_tx(3), ea.AdvancePhase) }
test happy_adminchannel_advancephase_4() { mock.election_validate(minimal_tx(4), ea.AdvancePhase) }
test happy_adminchannel_advancephase_5() { mock.election_validate(minimal_tx(5), ea.AdvancePhase) }
test happy_adminchannel_advancephase_6() { mock.election_validate(minimal_tx(6), ea.AdvancePhase) }
test happy_adminchannel_advancephase_7() { mock.election_validate(minimal_tx(7), ea.AdvancePhase) }
test happy_adminchannel_advancephase_8() { mock.election_validate(minimal_tx(8), ea.AdvancePhase) }
test happy_adminchannel_advancephase_9() { mock.election_validate(minimal_tx(9), ea.AdvancePhase) }

// ====================
// EndElection
// ====================

fn output10() -> Output {
  Output {
    address: mock.admin_address(), // admin's personal wallet
    value: assets.zero,
    datum: NoDatum,
    reference_script: None,
  }
}

fn tx10() -> Transaction {
  Transaction {
    ..transaction.placeholder,
    mint: mock.burn_stt("admin"),
    inputs: [minimal_input(10)],
    outputs: [output10()],
    extra_signatories: [mock.admin_vkh()],
  }
}

test happy_adminchannel_endelection() {
  mock.election_validate(tx10(), ea.EndElection)
}
