use aiken/crypto.{VerificationKeyHash}
use election/types/phase.{ElectionPhase}
use election/types/record.{PublicRecord}
use election/types/channel_id.{ChannelId}

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
  trace @"get_channel_id"
  when state is {
    None -> "admin" // first tx (InitElection)
    Some(AdminChannel(_)) -> "admin"
    Some(SubChannel(sub_state)) -> sub_state.channel_id
  }
}

// Types must match: both AdminChannel or both SubChannel.
pub fn get_new_records(
  state: ChannelState,
  continuation: ChannelState,
) -> List<PublicRecord> {
  trace @"get_new_records"
  when state is {
    AdminChannel(_) -> {
      expect AdminChannel(cont_state) = continuation
      cont_state.new_records
    }   
    SubChannel(_) -> {
      expect SubChannel(cont_state) = continuation
      cont_state.new_records
    }   
  }
}
