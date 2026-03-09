use cardano/transaction.{OutputReference, Transaction}

use election

// Mock one-shot UTxO.
pub fn mock_oneshot_ref() -> OutputReference {
  OutputReference { transaction_id: #"c0ffee", output_index: 0 }
}

// Helper to test both mint and spend validators on the same transaction,
// automatically parameterizing with the one-shot UTxO.
pub fn validate_election_action(
  inputs: List<Input>,
  redeemer: Option<ElectionAction>,
  tx: Transaction,
) {
  let oref = mock_oneshot_ref()

  // mint is run once per policy_id, so only once in these tests
  let mint_passes = election.election.mint(
    oref,
    redeemer,
    policy_id,
    tx
  )

  // spend is run once per input consumed
  let all_spends_pass =
    tx.inputs |>
    election.election.spend(
      oref,
      input.output.datum,
      redeemer,
      input.output,
      tx
    )

  mint_passes && all_spends_pass
}
