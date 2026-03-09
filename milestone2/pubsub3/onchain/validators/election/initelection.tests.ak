use aiken/collection/list
use cardano/address.{Address, VerificationKey}
use cardano/assets
use cardano/transaction.{Input, NoDatum, Output, OutputReference, Transaction}

pub const own_hash = #"dead"
pub const other_hash = #"c0ffee"
pub const beneficiary_keyhash = #"c001"

pub fn beneficiary_address() {
  keyhash_address(beneficiary_keyhash)
}

pub fn keyhash_address(keyhash: ByteArray) {
  Address {
    payment_credential: VerificationKey(keyhash),
    stake_credential: None,
  }
}

validator simple_oneshot(utxo_ref: OutputReference) {
  mint(_r: Void, _policy_id: ByteArray, self: Transaction) {
    let Transaction { inputs, .. } = self
    when list.find(inputs, fn(input) { input.output_reference == utxo_ref }) is {
      Some(_) -> True
      None -> False
    }
  }
  // TODO is this needed in current aiken?
  else(_) {
    fail
  }
}

// based on test_simple_oneshot from the aiken src code
test test_wip_initelection() {
  let output =
    Output {
      address: beneficiary_address(),
      value: assets.zero,
      datum: NoDatum,
      reference_script: None,
    }

  let mint =
    assets.from_asset(policy_id: own_hash, asset_name: "testtoken", quantity: 1)
  let utxo = OutputReference { transaction_id: "", output_index: 0 }

  let input = Input { output_reference: utxo, output }

  let tx =
    Transaction {
      // TODO does placeholder include ADA for fee? or is that ignored?
      ..transaction.placeholder,
      mint: mint,
      extra_signatories: [other_hash],
      inputs: [input],
    }

  simple_oneshot.mint(utxo, Void, own_hash, tx) == True
}
