use aiken/collection/list

use cardano/assets.{PolicyId}
use cardano/transaction.{
  InlineDatum,
  Input, OutputReference, Transaction
}

use election
use election/action.{ElectionAction}
use election/state.{ChannelState}

// Mock one-shot UTxO.
pub fn mock_oneshot_ref() -> OutputReference {
  OutputReference { transaction_id: #"c0ffee", output_index: 0 }
}

pub fn mock_policy_id() -> PolicyId {
  #"c001"
}

// Aiken explicitly disallows importing validators into reusable test modules,
// so to get around it I just test the top-level functions the validator would
// call with the same arguments. This tests both mint and spend validators on
// the same transaction, automatically parameterizing with the one-shot UTxO.
pub fn mock_validate(
  tx: Transaction,
  redeemer: ElectionAction,
) {
  let oref = mock_oneshot_ref()
  let policy_id = mock_policy_id()

  // mint is run once per policy_id, so only once in these tests
  let mint_passes = mock_mint(
    oref,
    redeemer,
    policy_id,
    tx
  )

  // spend is run once per input consumed, and doesn't use oneshot_ref
  let all_spends_pass = list.all(
    tx.inputs,
    fn(input) {
      // TODO does this handle the NoDatum (None) case properly?
      expect InlineDatum(data) = input.output.datum
      expect datum: Option<ChannelState> = data
      mock_spend(
        datum,
        redeemer,
        input.output_reference,
        tx
      )
    }
  )

  mint_passes && all_spends_pass
}

pub fn mock_mint(
  oneshot_ref: OutputReference,
  redeemer: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction
) -> Bool {
  election.validate_mint(oneshot_ref, redeemer, policy_id, tx)
}

pub fn mock_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  election.validate_spend(datum, redeemer, own_ref, tx)
}
