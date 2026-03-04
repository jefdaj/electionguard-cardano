use aiken/crypto.{VerificationKeyHash}
// use cardano/transaction.{InlineDatum, Output}

use election/record.{PublicRecord}

pub type ChannelId = ByteArray

pub type ChannelState {
  AdminChannel(AdminChannelState)
  SubChannel(SubChannelState)
}

pub type AdminChannelState {

  // There can only be one admin channel per election.
  // It has the implicit channel_id "admin".

  // This is its "publisher" key, but also allows other admin actions.
  admin: VerificationKeyHash,

  // Only the admin can mint and burn subchannels.
  subchannels: List<ChannelId>,

  // Just the latest batch of records; have to index the STT asset history to get the full list.
  // Should be set to [] when doing any non-publish transaction.
  new_records: List<PublicRecord>,

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
