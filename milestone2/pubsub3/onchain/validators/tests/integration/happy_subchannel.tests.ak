// Second integration test: simplest happy path through the lifecycle of a subchannel.
// Builds on the admin channel tests in validators/tests/integration/minimal.tests.ak.

use cardano/transaction.{Input, InlineDatum, NoDatum, Output, OutputReference, Transaction}
// TODO can't import test modules? use tests/integration/happy_adminchannel
use tests/mock

// ===============================
// minimal lifecycle: mint, burn
// ===============================

// TODO fork off from:   (2, ep.ElectionConfigPhase(ep.ConfigOnboardingPhase)),
// TODO merge back into: (9, ep.ElectionFinalizePhase                        ),

fn mint_tx() -> Transaction {
  // let input = happy_adminchannel.minimal_state(2)
  Transaction {
    ..transaction.placeholder,
    inputs: [],
    outputs: [],
    extra_signatories: [mock.admin_vkh()],
  }
}

test happy_subchannel_minimal_mint() {
  True
}

test happy_subchannel_minimal_burn() {
  True
}
