use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/assets.{PolicyId}
use cardano/transaction.{Transaction, OutputReference}
use election/stt.{find_admin_stt_output, get_input_state}
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
  expect AdminChannel(state) = get_input_state(None, own_ref, tx)
  state.admin
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
