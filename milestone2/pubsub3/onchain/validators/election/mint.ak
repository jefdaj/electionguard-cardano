use aiken/collection/dict
use aiken/collection/list
use cardano/assets.{PolicyId, has_any_nft}
use cardano/transaction.{OutputReference, Transaction}
use election/stt.{full_stt_name, get_policy_id, count_tokens_in_outputs}
use election/types/channel.{ChannelId}

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

// Allow only if all quantities for this policy are negative (burning)
pub fn tx_only_burns(policy_id: PolicyId, tx: Transaction) -> Bool {
  trace @"tx_only_burns"
  assets.tokens(tx.mint, policy_id)
    |> dict.to_pairs()
    |> list.all(fn(pair) { pair.2nd < 0 })
}

// Whether a TX burns all tokens, leaving none in the outputs.
// Note this is different from RmSubChannels, which leaves the admin STT.
pub fn tx_burns_all(own_ref: OutputReference, tx: Transaction) -> Bool {
  trace @"tx_burns_all"
  let policy_id = get_policy_id(own_ref, tx.inputs)
  let tokens_out = count_tokens_in_outputs(tx.outputs, policy_id)
  (tokens_out == 0) ?
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

// Confirm that none of our tokens are being minted or burned.
pub fn no_mints_for_policy(policy_id: PolicyId, tx: Transaction) -> Bool {
  trace @"no_mints_for_policy"
  ! has_any_nft(tx.mint, policy_id)
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
