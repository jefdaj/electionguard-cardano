// This lib will have less confusing names if you import it qualified:
//
// use tests/mock
// mock.oneshot_ref()
// mock.policy_id()
// mock.election_validate(...)
//

use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}

use cardano/address.{Script, Address, VerificationKey}
use cardano/assets.{PolicyId}
use cardano/transaction.{
  InlineDatum,
  Input, OutputReference, Transaction,
}

use election
use election/action.{ElectionAction}
use election/state.{ChannelState}

pub fn admin_vkh() -> VerificationKeyHash {
  #"abc123"
}

pub fn admin_address() -> Address {
  Address {
    payment_credential: VerificationKey(admin_vkh()),
    stake_credential: None,
  }
}

pub fn oneshot_oref() -> OutputReference {
  OutputReference { transaction_id: #"c0ffee", output_index: 0 }
}

pub fn policy_id() -> PolicyId {
  #"c001"
}

pub fn script_address() -> Address {
  Address {
    payment_credential: Script(policy_id()),
    stake_credential: None,
  }
}


// Aiken explicitly disallows importing validators into reusable test modules,
// so to get around it I just test the top-level functions the validator would
// call with the same arguments. This tests both mint and spend validators on
// the same transaction, automatically parameterizing with the one-shot UTxO.
pub fn election_validate(
  tx: Transaction,
  redeemer: ElectionAction,
) {

  // mint is run once per policy_id, so only once in these tests
  let mint_passes = election_validate_mint(
    oneshot_oref(),
    redeemer,
    policy_id(),
    tx
  )

  // spend is run once per input consumed, and doesn't use oneshot_ref
  let all_spends_pass = list.all(
    tx.inputs,
    fn(input) {
      let datum: Option<ChannelState> = when input.output.datum is {
	InlineDatum(data) -> {
	  expect state: ChannelState = data
	  Some(state)
	}
	_ -> None
      }
      election_validate_spend(
        datum,
        redeemer,
        input.output_reference,
        tx
      )
    }
  )

  mint_passes && all_spends_pass
}

fn election_validate_mint(
  oneshot_ref: OutputReference,
  redeemer: ElectionAction,
  policy_id: PolicyId,
  tx: Transaction
) -> Bool {
  election.validate_mint(oneshot_ref, redeemer, policy_id, tx)
}

fn election_validate_spend(
  datum: Option<ChannelState>,
  redeemer: ElectionAction,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  election.validate_spend(datum, redeemer, own_ref, tx)
}
