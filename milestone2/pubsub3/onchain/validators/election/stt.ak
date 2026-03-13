use aiken/primitive/string
use aiken/collection/dict
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/address.{Script, Address}
use cardano/assets.{PolicyId, has_any_nft}
use cardano/transaction.{Transaction, Input, InlineDatum, Output, OutputReference}
use election/utils.{tx_signed_by}

use config

use election/state.{
  ChannelId, ChannelState,
  AdminChannel, AdminChannelState,
  SubChannel, get_channel_id,
}

// TODO is it important to check that only one STT is sent to a given output?

// Whether a transaction mints the required amount of a token.
pub fn tx_mints(
  tx: Transaction,
  policy_id: PolicyId,
  token_name: ByteArray,
  amount: Int,
) -> Bool {
  trace @"tx_mints"
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
  trace @"tx_mints_all"
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
  trace @"tx_does_not_mint"
  let Transaction { mint, .. } = tx
  let minted = mint |> assets.tokens(policy_id) |> dict.to_pairs()
  minted == []
}

// From Rhys's Aiken Language Test Lib 3/5 video
pub fn scriptAddress(hash: ByteArray) -> Address {
  trace @"scriptAddress"
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
  trace @"tx_sends_token_to_addr"
  tx.outputs
  |> list.find(fn(output) {
       output.address == addr &&
       assets.quantity_of(output.value, policy_id, token_name) >= min_quantity
     })
}

// Confirm that none of our tokens are being minted or burned.
pub fn no_mints_for_policy(policy_id: PolicyId, tx: Transaction) -> Bool {
  trace @"no_mints_for_policy"
  ! has_any_nft(tx.mint, policy_id)
}

pub fn full_stt_name(channel_id: ChannelId) -> ByteArray {
  trace @"full_stt_name"
  let prefix = string.from_bytearray(config.stt_prefix)
  let id = string.from_bytearray(channel_id)
  let full_name = string.join([prefix, id, @"channel", @"state"], @"-")
  // trace @"full_name" : full_name
  string.to_bytearray(full_name)
}

// Note that you can set state to None to use this in the admin mint validator.
// TODO is that actually true? or did it fail?
pub fn get_stt_name(state: Option<ChannelState>) -> ByteArray {
  trace @"get_stt_name"
  let channel_id = get_channel_id(state)
  // trace @"string channel_id" : string.from_bytearray(channel_id)
  full_stt_name(channel_id)
}

pub fn exact_channels_minted(
  tx: Transaction,
  policy_id: PolicyId,
  channel_ids: List<ChannelId>
) -> Bool {
  trace @"exact_channels_minted"
  check_exact_mint_burn(tx, policy_id, channel_ids, 1)
}

pub fn exact_channels_burned(
  tx: Transaction,
  policy_id: PolicyId,
  channel_ids: List<ChannelId>
) -> Bool {
  trace @"exact_channels_burned"
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
  // token_names: List<AssetName>,
  channel_ids: List<ChannelId>,
  quantity: Int,
) -> Bool {
  trace @"check_exact_mint_burn"

  let token_names = list.map(channel_ids, fn(i) { full_stt_name(i) })

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
  trace @"find_admin_stt_output"
  let stt_name = full_stt_name("admin")
  find_input_with_token(tx, policy_id, stt_name)
}

fn find_input_with_token(
  tx: Transaction,
  policy_id: ByteArray,
  token_name: ByteArray,
) -> Option<OutputReference> {
  trace @"find_input_with_token"
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
  trace @"admin_authorized_tx"
  when find_admin_stt_output(tx, policy_id) is {
    Some(_) -> True
    None    -> False
  }
}

pub fn get_policy_id(
  own_ref: OutputReference,
  inputs: List<Input>
) -> PolicyId {
  trace @"get_policy_id"
  expect Some(own_input) = inputs |> transaction.find_input(own_ref)
  expect Script(policy_id) = own_input.output.address.payment_credential
  // trace @"policy_id" : policy_id
  policy_id
}

/// Find all policy IDs for tokens with the given name across all transaction outputs.
/// Returns a list of unique policy IDs that have tokens with the specified name.
pub fn find_policy_ids_by_token_name(
  tx: Transaction,
  name: ByteArray,
) -> List<ByteArray> {
  trace @"find_policy_ids_by_token_name"
  tx.outputs
    |> list.flat_map(
         fn(output) {
           output.value
             |> assets.flatten()
             |> list.filter_map(
                  fn(asset) {
                    let (policy_id, token_name, _quantity) = asset
                    if token_name == name {
                      Some(policy_id)
                    } else {
                      None
                    }
                  },
                )
         },
       )
    |> list.unique()
}

// This can't be done the usual way because there's no input STT.
pub fn get_initial_state(
  tx: Transaction,
) -> AdminChannelState {
  trace @"get_initial_state"
  let stt_name = full_stt_name("admin")
  let matching_datums =
    tx.outputs
      |> list.filter_map(
           fn(output) {
             let has_token =
               output.value
                 |> assets.flatten()
                 |> list.any(
                      fn(asset) {
                        let (_, token_name, _) = asset
                        token_name == stt_name
                      },
                    )

             if has_token {
               when output.datum is {
                 InlineDatum(data) -> Some(data)
                 _ -> None
               }
             } else {
               None
             }
           },
         )
  expect [datum] = matching_datums
  expect Some(AdminChannel(init_state)) = datum
  init_state
}


// TODO rename stt -> own?
// The state is optional because there isn't one during InitElection.
// TODO find instead of get? not sure if None is helpful
pub fn get_stt_state(
  datum: Option<ChannelState>, // TODO remove option because can't handle initial state
  outputs: List<Output>,
  policy_id: PolicyId,
) -> Option<ChannelState> {
  trace @"get_stt_state"
  let stt_name = get_stt_name(datum)
  // Find the input containing the STT
  expect Some(stt_output) =
    list.find(outputs, fn(output) {
      assets.has_nft(output.value, policy_id, stt_name)
    })
  // trace @"stt_output" : stt_output
  when stt_output.datum is {
    InlineDatum(datum) -> {
      expect state: Option<ChannelState> = datum
      state
    }
    _ -> None
  }
}

pub fn get_input_state(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> ChannelState {
  trace @"get_input_state"
  let input_outputs = list.map(tx.inputs, fn(input) { input.output })
  let policy_id = get_policy_id(own_ref, tx.inputs)
  expect Some(state) = get_stt_state(datum, input_outputs, policy_id)
  state
}


// The state is optional because there isn't one during InitElection.
pub fn get_continuation_state(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> ChannelState {
  trace @"get_continuation_state"
  let policy_id = get_policy_id(own_ref, tx.inputs)
  expect Some(state) = get_stt_state(datum, tx.outputs, policy_id)
  state
}

pub fn get_publisher_vkh(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> VerificationKeyHash {
  trace @"get_publisher_vkh"
  let state = get_input_state(datum, own_ref, tx)
  when state is {
    AdminChannel(admin_state) -> admin_state.admin
    SubChannel(sub_state) -> sub_state.publisher
  }
}

pub fn get_admin_vkh(
  own_ref: OutputReference,
  tx: Transaction,
) -> VerificationKeyHash {
  trace @"get_admin_vkh"
  expect AdminChannel(state) = get_input_state(None, own_ref, tx)
  state.admin
}

pub fn publisher_signed(
  datum: Option<ChannelState>,
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"publisher_signed"
  let pub_vkh = get_publisher_vkh(datum, own_ref, tx)
  let pub_sig = tx_signed_by(tx, pub_vkh) ?
  pub_sig
}

// TODO move to different module?
pub fn admin_signed(
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"admin_signed"
  let admin_vkh = get_admin_vkh(own_ref, tx)
  let admin_sig = tx_signed_by(tx, admin_vkh) ?
  admin_sig
}

// This prevents more than one STT being sent to a given UTxO.
// It may not be strictly required, but simplifies the mental model.
pub fn channels_kept_separate(
  own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"channels_kept_separate"
  // trace @"checking each output has at most 1 channel STT"
  let policy_id = get_policy_id(own_ref, tx.inputs)
  list.all(
    tx.outputs,
    fn(output) {
      let stt_count =
        output.value
          |> assets.tokens(policy_id)
          |> dict.size()

      // trace @"stt_count at output": stt_count
      (stt_count <= 1) ?
    },
  )
}

pub fn correct_n_channels_updated(
  own_ref: OutputReference,
  tx: Transaction,
  channels: List<ChannelId>,
) -> Bool {
  trace @"correct_n_channels_updated"

  let expected = list.length(channels) + 1 // +1 for admin STT

  let policy_id = get_policy_id(own_ref, tx.inputs)
  // Count channel STTs being spent.
  let stt_count = {
    // trace @"counting channel STTs in inputs"
    count_tokens_in_inputs(tx.inputs, policy_id)
  }
  // trace @"stt_count" : stt_count

  (stt_count == expected) ?
}

// Generic: count tokens in a list of outputs
pub fn count_tokens_in_outputs(
  outputs: List<Output>,
  policy_id: PolicyId,
) -> Int {
  trace @"count_tokens_in_outputs"
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
  trace @"count_tokens_in_inputs"
  inputs
    |> list.map(fn(input) { input.output })
    |> count_tokens_in_outputs(policy_id)
}
