// This lib will have less confusing names if you import it qualified:
//
// use tests/mock
// mock.oneshot_ref()
// mock.policy_id()
// mock.election_validate(...)
//

use aiken/crypto.{Blake2b_224, Hash}
use aiken/primitive/string
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}

use cardano/assets.{Value}
use cardano/address.{Script, Address, VerificationKey}
use cardano/assets.{PolicyId}
use cardano/transaction.{
  Datum, NoDatum, InlineDatum,
  Input, Output, OutputReference, Transaction,
}

use election
use election/action.{ElectionAction}
use election/state.{
  ChannelId, ChannelState,
  AdminChannel, AdminChannelState,
  SubChannel, SubChannelState
}
use election/stt

pub fn vkh(seed: ByteArray) -> Hash<Blake2b_224, ByteArray> {
  crypto.blake2b_224(seed)
}

pub fn admin_vkh() -> VerificationKeyHash {
  vkh(string.to_bytearray(@"admin"))
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
) -> Bool {

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
	  expect state: Option<ChannelState> = data
	  state
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

pub fn admin_datum(state: AdminChannelState) -> Datum {
  InlineDatum(Some(AdminChannel(state)))
}

pub fn subchannel_datum(state: SubChannelState) -> Datum {
  InlineDatum(Some(SubChannel(state)))
}

pub fn mint_stt(channel_id: ChannelId) -> Value {
  let stt_name = stt.full_stt_name(channel_id)
  trace @"mint_stt stt_name" : string.from_bytearray(stt_name)
  assets.from_asset(
    policy_id: policy_id(),
    asset_name: stt_name,
    quantity: 1
  )
}

pub fn mint_stts(channel_ids: List<ChannelId>) -> Value {
  let values = list.map(channel_ids, mint_stt)
  list.foldl(
    values,
    assets.zero,
    fn(val, acc) { assets.merge(val, acc) }
  )
}

pub fn burn_stts(channel_ids: List<ChannelId>) -> Value {
  let values = list.map(channel_ids, burn_stt)
  list.foldl(
    values,
    assets.zero,
    fn(val, acc) { assets.merge(val, acc) }
  )
}

// It seems counterintuitive to me to call the continuing value at each stage a
// "mint" when it hasn't changed, so this is an alias to make it clearer.
pub const stt_value = mint_stt

pub fn burn_stt(channel_id: ChannelId) -> Value {
  assets.from_asset(
    policy_id: policy_id(),
    asset_name: stt.full_stt_name(channel_id),
    quantity: -1
  )
}

pub fn oneshot_output() -> Output {
  Output {
    address: admin_address(), // admin's personal wallet
    value: assets.zero,
    datum: NoDatum,
    reference_script: None,
  }
}

pub fn oneshot_input() -> Input {
  Input {
    output_reference: oneshot_oref(),
    output: oneshot_output()
  }
}
