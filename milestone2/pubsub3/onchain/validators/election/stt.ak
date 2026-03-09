use aiken/collection/dict
use aiken/collection/list
use aiken/crypto.{ScriptHash, VerificationKeyHash}
use cardano/address.{Script, Address}
use cardano/assets.{AssetName, PolicyId, has_any_nft}
use cardano/transaction.{Transaction, Input, InlineDatum, Output, OutputReference}
use election/utils.{bytearray_join, tx_signed_by}

use config

use election/state.{
  ChannelId, ChannelState, AdminChannel, SubChannel,
  get_stt_name,
}

// TODO is it important to check that only one STT is sent to a given output?

// Whether a transaction mints the required amount of a token.
pub fn tx_mints(
  tx: Transaction,
  policy_id: PolicyId,
  token_name: ByteArray,
  amount: Int,
) -> Bool {
  let Transaction { mint, .. } = tx
  let policy_tokens = assets.tokens(mint, policy_id)

  when dict.get(policy_tokens, token_name) is {
    None -> amount == 0
    Some(actual_amount) -> actual_amount == amount
  }
}

// tx_mints mapped over a list of token names.
pub fn tx_mints_all(
  tx: Transaction,
  policy_id: PolicyId,
  token_names: List<ByteArray>,
  amount: Int,
) -> Bool {
  list.all(token_names, fn(token_name) {
    tx_mints(tx, policy_id, token_name, amount)
  })
}

// TODO name something better
// TODO implement in terms of tx_mints?
pub fn tx_does_not_mint(
  tx: Transaction,
  policy_id: PolicyId
) -> Bool {
  let Transaction { mint, .. } = tx
  let minted = mint |> assets.tokens(policy_id) |> dict.to_pairs()
  minted == []
}

// From Rhys's Aiken Language Test Lib 3/5 video
pub fn scriptAddress(hash: ByteArray) -> Address {
  let addr = Address {
    payment_credential: Script(hash),
    stake_credential: None,
  }
  addr
}

// TODO specialize this to mint(1), burn(-1), and no change(0)?
pub fn tx_sends_token_to_addr(
  tx: Transaction,
  policy_id: PolicyId,
  token_name: ByteArray,
  addr: Address,
  min_quantity: Int // TODO require exact quantity?
) -> Option<Output> {
  tx.outputs
  |> list.find(fn(output) {
       output.address == addr &&
       assets.quantity_of(output.value, policy_id, token_name) >= min_quantity
     })
}

// Confirm that none of our tokens are being minted or burned.
pub fn no_mints_for_policy(policy_id: PolicyId, tx: Transaction) -> Bool {
  ! has_any_nft(tx.mint, policy_id)
}

pub fn full_stt_name(channel_id: ChannelId) -> ByteArray {
  bytearray_join([config.stt_prefix, channel_id, "channel", "state"], "-")
}

pub fn exact_channels_minted(
  tx: Transaction,
  policy_id: PolicyId,
  channel_ids: List<ChannelId>
) -> Bool {
  check_exact_mint_burn(tx, policy_id, channel_ids, 1)
}

pub fn exact_channels_burned(
  tx: Transaction,
  policy_id: PolicyId,
  channel_ids: List<ChannelId>
) -> Bool {
  check_exact_mint_burn(tx, policy_id, channel_ids, -1)
}

/// Checks that exactly the specified tokens are minted (quantity = 1) or burned (quantity = -1)
///
/// # Arguments
/// * `tx` - The transaction to validate
/// * `policy_id` - The policy ID of the tokens to check
/// * `token_names` - List of asset names that should be minted/burned
/// * `quantity` - Either 1 (for minting) or -1 (for burning)
///
/// # Returns
/// * `True` if exactly those tokens are minted/burned with the correct quantity
/// * `False` otherwise
fn check_exact_mint_burn(
  tx: Transaction,
  policy_id: PolicyId,
  token_names: List<AssetName>,
  quantity: Int,
) -> Bool {
  // Extract the tokens for this policy from the mint field
  let minted_tokens =
    tx.mint
      |> assets.tokens(policy_id)
      |> dict.to_pairs()

  // Check that the number of minted tokens matches expected
  let count_matches = list.length(minted_tokens) == list.length(token_names)

  // Check that every expected token is present with correct quantity
  let all_tokens_present =
    list.all(
      token_names,
      fn(expected_name) {
        list.any(
          minted_tokens,
          fn(pair) {
            let Pair(actual_name, actual_quantity) = pair
            actual_name == expected_name && actual_quantity == quantity
          },
        )
      },
    )

  // Both conditions must be true
  count_matches && all_tokens_present
}

pub fn find_admin_stt_output(
  tx: Transaction,
  policy_id: PolicyId
) -> Option<OutputReference> {
  let stt_name = full_stt_name("admin")
  find_input_with_token(tx, policy_id, stt_name)
}

fn find_input_with_token(
  tx: Transaction,
  policy_id: ByteArray,
  token_name: ByteArray,
) -> Option<OutputReference> {
  when
    list.find(
      tx.inputs,
      fn(input: Input) {
        assets.quantity_of(input.output.value, policy_id, token_name) > 0
      },
    )
  is {
    Some(input) -> Some(input.output_reference)
    None -> None
  }
}

// Whether the admin authorized this transaction by spending the admin STT
// (and therefore also by signing, which is checked in the spend validator).
pub fn admin_authorized_tx(
  tx: Transaction,
  policy_id: PolicyId
) -> Bool {
  when find_admin_stt_output(tx, policy_id) is {
    Some(_) -> True
    None    -> False
  }
}

// TODO does needing script_addr imply I'm doing something wrong?
pub fn get_script_info(
  own_ref: OutputReference,
  tx: Transaction,
) -> (Address, ScriptHash) {
  expect Some(own_input) = tx.inputs |> transaction.find_input(own_ref)
  expect Script(policy_id) = own_input.output.address.payment_credential
  let script_addr = own_input.output.address
  (script_addr, policy_id)
}

// TODO rename stt -> own?
// The state is optional because there isn't one during InitElection.
// TODO find instead of get? not sure if None is helpful
pub fn get_stt_state(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> Option<ChannelState> {
  let (script_addr, policy_id) = get_script_info(own_ref, tx)
  let stt_name = get_stt_name(datum)
  // Find the output containing the STT
  expect Some(stt_output) =
    list.find(tx.outputs, fn(output) {
      output.address == script_addr &&
      assets.quantity_of(output.value, policy_id, stt_name) == 1
    })
  when stt_output.datum is {
    InlineDatum(datum) -> {
      expect state: ChannelState = datum
      Some(state)
    }
    _ -> None
  }
}

// The state is optional because there isn't one during InitElection.
pub fn get_continuation_state(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> ChannelState {
  expect Some(cont_state) = get_stt_state(datum, own_ref, tx)
  cont_state
}

pub fn get_publisher_vkh(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> VerificationKeyHash {
  expect Some(state) = get_stt_state(datum, own_ref, tx)
  when state is {
    AdminChannel(admin_state) -> admin_state.admin
    SubChannel(sub_state) -> sub_state.publisher
  }
}

pub fn get_admin_vkh(
  own_ref: OutputReference,
  tx: Transaction,
) -> VerificationKeyHash {
  expect Some(AdminChannel(state)) = get_stt_state(None, own_ref, tx)
  state.admin
}

pub fn publisher_signed(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  let pub_vkh = get_publisher_vkh(datum, own_ref, tx)
  tx_signed_by(tx, pub_vkh)
}

pub fn admin_signed(
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  let admin_vkh = get_admin_vkh(own_ref, tx)
  tx_signed_by(tx, admin_vkh)
}

// This prevents more than one STT being sent to a given UTxO.
// It may not be strictly required, but simplifies the mental model.
pub fn channels_kept_separate(
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"checking each output has at most 1 channel STT"
  let (_, policy_id) = get_script_info(own_ref, tx)
  list.all(
    tx.outputs,
    fn(output) {
      let stt_count =
        output.value
          |> assets.tokens(policy_id)
          |> dict.size()

      trace @"stt_count at output": stt_count
      (stt_count <= 1) ?
    },
  )
}

pub fn correct_n_channels_updated(
  own_ref: OutputReference,
  tx: Transaction,
  channels: List<ChannelId>,
) -> Bool {

  let expected = list.length(channels) + 1 // +1 for admin STT

  let (_, policy_id) = get_script_info(own_ref, tx)
  // Count channel STTs being spent.
  let stt_count = {
    trace @"counting channel STTs in inputs"
    count_tokens_in_outputs(tx.outputs, policy_id)
  }

  (stt_count == expected) ?
}

// Generic: count tokens in a list of outputs
pub fn count_tokens_in_outputs(
  outputs: List<Output>,
  policy_id: PolicyId,
) -> Int {
  outputs
    |> list.foldl(
        0,
        fn(output, count) {
          let token_count =
            output.value
              |> assets.tokens(policy_id)
              |> dict.size()

          count + token_count
        },
      )
}

// Adapter: count tokens in transaction inputs
pub fn count_tokens_in_inputs(
  inputs: List<Input>,
  policy_id: PolicyId,
) -> Int {
  inputs
    |> list.map(fn(input) { input.output })
    |> count_tokens_in_outputs(policy_id)
}
