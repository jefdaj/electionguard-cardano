use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
// use cardano/transaction.{InlineDatum, Output}

use election/phase.{ElectionPhase}
use election/record.{PublicRecord}

use election/utils.{bytearray_join, remove_elements}

use config

// TODO rename Channel?

pub type ChannelId = ByteArray

pub type ChannelState {
  AdminChannel(AdminChannelState)
  SubChannel(SubChannelState)
}

pub type AdminChannelState {

  // There can only be one admin channel per election.
  // It has the implicit channel_id "admin".
  // TODO any reason to add an actual channel_id field here too?

  // This is its "publisher" key, but also allows other admin actions.
  admin: VerificationKeyHash,

  // Only the admin can mint and burn subchannels.
  subchannels: List<ChannelId>,

  // Just the latest batch of records; have to index the STT asset history to get the full list.
  // Should be set to [] when doing any non-publish transaction.
  new_records: List<PublicRecord>,

  // Tracks the overall phase of the election for display in the UI.
  // Could be extended later for use in:
  // - syncing channels at certain points
  // - restricting what can be posted at which points
  // - setting min/max time intervals per phase
  phase: ElectionPhase,

  // For detecting rollbacks or errors
  seq: Int
}

pub type SubChannelState {

  // channel_id and publisher are set by the admin and can't be edited.
  // TODO later, let the admin change the publisher key?
  channel_id: ChannelId,
  publisher: VerificationKeyHash,

  // Works the same as on the admin channel.
  new_records: List<PublicRecord>,

  // Works the same as on the admin channel.
  seq: Int
}

pub fn get_channel_id(state: Option<ChannelState>) -> ChannelId {
  when state is {
    None -> "admin"
    Some(AdminChannel(_)) -> "admin"
    Some(SubChannel(sub_state)) -> sub_state.channel_id
  }
}

// Note that you can set state to None to use this in the admin mint validator.
// TODO is that weird and confusing?
pub fn get_stt_name(state: Option<ChannelState>) -> ByteArray {
  let channel_name = get_channel_id(state)
  bytearray_join([config.stt_prefix, channel_name, "channel"], "-")
}

pub fn get_admin_stt_name() -> ByteArray {
  get_stt_name(None)
}

// TODO remove?
pub fn extract_admin_state(state: Option<ChannelState>) -> Option<AdminChannelState> {
  when state is {
    None -> None
    Some(AdminChannel(admin_state)) -> Some(admin_state)
    Some(SubChannel(_)) -> None
  }
}

// TODO remove?
pub fn extract_subchannel_state(state: ChannelState) -> Option<SubChannelState> {
  when state is {
    SubChannel(subchannel_state) -> Some(subchannel_state)
    AdminChannel(_) -> None
  }
}

// Note that this will work even if it makes an invalid list of subchannels.
// TODO should those checks go here too?
pub fn add_subchannels(old_state: AdminChannelState, new_channels: List<ChannelId>) -> AdminChannelState {
  AdminChannelState(
    old_state.admin, // should be unchanged
    list.concat(new_channels, old_state.subchannels), // TODO sort here?
    [], // should be reset on each non-post tx
    old_state.phase,
    old_state.seq + 1 // should be incremented
  )
}

// Note that this doesn't check whether the channels removed make sense.
// TODO should those checks also go here?
pub fn rm_subchannels(old_state: AdminChannelState, channels_to_rm: List<ChannelId>) -> AdminChannelState {
  AdminChannelState(
    old_state.admin, // should be unchanged
    remove_elements(old_state.subchannels, channels_to_rm),
    [], // should be reset on each non-post tx
    old_state.phase,
    old_state.seq + 1 // should be incremented
  )
}

// Note that this doesn't check validity of the records
// TODO should those checks also go here?
pub fn post_public_records(old_state: ChannelState, records: List<PublicRecord>) -> ChannelState {
  when old_state is {
    AdminChannel(old) -> AdminChannel(AdminChannelState(
      old.admin,
      old.subchannels,
      records, // should replace the old list
      old.phase, // TODO should this be allowed to transition?
      old.seq + 1, // should be incremented
    ))
    SubChannel(old) -> SubChannel(SubChannelState(
      old.channel_id,
      old.publisher,
      records, // should be replaced
      old.seq + 1, // should be incremented
    ))
  }
}

// TODO remove this fn for now since it's not helping DRY anything out
// TODO rename old_publisher to reflect admin/publisher fields?
// pub fn publisher_unchanged(
//   old_publisher: VerificationKeyHash,
//   stt_output: Output
// ) -> Bool {
//   expect InlineDatum(new_datum) = stt_output.datum
//   // expect new_state: ChannelState = new_datum
//   when new_state is {
//     AdminChannel{ .. } -> {
//       expect AdminChannelState { admin, .. } = new_state
//       admin == old_publisher
//     }
//     SubChannel{ .. } -> {
//       expect SubChannelState { publisher, .. } = new_state
//       publisher == old_publisher
//     }
//   }
// }

// TODO also remove this and do separate checks for now
// pub fn sequence_incremented(
//   old_seq: Int,
//   stt_output: Output
// ) -> Bool {
//   expect InlineDatum(new_datum) = stt_output.datum
//   expect new_state: ChannelState = new_datum
//   new_state.seq == (old_seq + 1)
// }
