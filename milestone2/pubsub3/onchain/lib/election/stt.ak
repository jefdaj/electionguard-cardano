use aiken/collection/dict
use aiken/collection/list
use cardano/address.{Script, Address}
use cardano/assets.{AssetName, PolicyId, has_any_nft}
use cardano/transaction.{Transaction, Output}
use election/utils.{bytearray_join}

use config

use election/state.{ChannelId}

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

// TODO move to stt.ak
pub fn full_stt_name(channel_id: ChannelId) -> ByteArray {
  bytearray_join([config.stt_prefix, channel_id, "channel"], "-")
}

pub fn check_exact_subchannels_minted(
  tx: Transaction,
  policy_id: PolicyId,
  channel_ids: List<ChannelId>
) -> Bool {
  check_exact_mint_burn(tx, policy_id, channel_ids, 1)
}

pub fn check_exact_subchannels_burned(
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
