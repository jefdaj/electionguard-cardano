use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/assets.{PolicyId}
use cardano/transaction.{Transaction, OutputReference}
use election/stt.{find_admin_stt_output, full_stt_name, get_input_state}
use election/types/channel.{ChannelState, AdminChannel, SubChannel}

// Whether a transaction was signed by the required key.
pub fn tx_signed_by(tx: Transaction, signer: VerificationKeyHash) -> Bool {
  trace @"tx_signed_by"
  list.has(tx.extra_signatories, signer)
}

// Whether the admin authorized this transaction by spending the admin STT
// (and therefore also by signing, which is checked in the spend validator).
pub fn admin_authorized_spend(
  tx: Transaction,
  policy_id: PolicyId
) -> Bool {
  trace @"admin_authorized_tx"
  when find_admin_stt_output(tx, policy_id) is {
    Some(_) -> True
    None    -> False
  }
}

pub fn get_admin_vkh(
  own_ref: OutputReference,
  tx: Transaction,
) -> VerificationKeyHash {
  trace @"get_admin_vkh"
  // TODO use find_admin_stt_output instead?
  let stt_name = full_stt_name("admin")
  expect AdminChannel(state) = get_input_state(own_ref, tx, stt_name)
  state.admin
}

pub fn get_publisher_vkh(
  state: ChannelState,
  // own_ref: OutputReference,
  // tx: Transaction,
) -> VerificationKeyHash {
  trace @"get_publisher_vkh"
  when state is {
    AdminChannel(admin_state) -> admin_state.admin
    SubChannel(sub_state) -> sub_state.publisher
  }
}

pub fn publisher_signed(
  state: ChannelState,
  // own_ref: OutputReference,
  tx: Transaction,
) -> Bool {
  trace @"publisher_signed"
  let pub_vkh = get_publisher_vkh(state)
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
