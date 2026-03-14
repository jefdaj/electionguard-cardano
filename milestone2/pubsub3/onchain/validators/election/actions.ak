use aiken/collection/list
use election/types/channel.{ChannelId, ChannelState, AdminChannel, AdminChannelState, SubChannel, SubChannelState}
use election/types/phase.{ElectionPhase}
use election/types/record.{PublicRecord}
use election/utils.{remove_elements}

// Note that this will work even if it makes an invalid list of subchannels.
// TODO should those checks go here too?
pub fn add_subchannels(
  old_state: AdminChannelState,
  new_channels: List<ChannelId>,
  new_phase: ElectionPhase
) -> AdminChannelState {
  trace @"add_subchannels"
  AdminChannelState(
    old_state.admin, // should be unchanged
    list.concat(new_channels, old_state.subchannels), // TODO sort here? reverse order?
    [], // should be reset on each non-post tx
    new_phase, // TODO should this be validated here rather than separately?
    old_state.seq + 1 // should be incremented
  )
}

// Note that this doesn't check whether the channels removed make sense.
// TODO should those checks also go here?
pub fn rm_subchannels(
  old_state: AdminChannelState,
  channels_to_rm: List<ChannelId>,
  new_phase: ElectionPhase
) -> AdminChannelState {
  trace @"rm_subchannels"
  AdminChannelState(
    old_state.admin, // should be unchanged
    remove_elements(old_state.subchannels, channels_to_rm),
    [], // should be reset on each non-post tx
    new_phase, // TODO should this be validated here rather than separately?
    old_state.seq + 1 // should be incremented
  )
}

// Note that this doesn't check validity of the records or new phase
// TODO should those checks also go here?
pub fn post_public_records(
  old_state: ChannelState,
  records: List<PublicRecord>,
  phase: Option<ElectionPhase>
) -> ChannelState {
  trace @"post_public_records"
  when old_state is {
    AdminChannel(old) -> AdminChannel(AdminChannelState(
      old.admin,
      old.subchannels,
      records, // should replace the old list
      when phase is {
        Some(new_phase) -> new_phase
        None -> old.phase
      },
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

pub fn advance_phase(state: AdminChannelState, cont_phase: ElectionPhase) -> AdminChannelState {
  AdminChannelState {
    ..state,
    new_records: [],
    phase: cont_phase,
    seq: state.seq + 1
  }
}
