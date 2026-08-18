use aiken/collection/list
use aiken/primitive/bytearray
use aiken/crypto.{VerificationKeyHash}
use election/types/channel_id.{ChannelId}
use election/types/channel.{ChannelState, AdminChannel, AdminChannelState, SubChannel, SubChannelState}
use election/types/ipfs_node.{IpfsNode}
use election/types/phase.{ElectionPhase, ElectionConfigPhase, ConfigAnnouncePhase}
use election/types/record.{PublicRecord}
use election/utils.{remove_elements}

pub fn init_election(admin: VerificationKeyHash) -> AdminChannelState {
  AdminChannelState {
    admin: admin,
    ipfs_node: None,
    subchannels: [],
    new_records: [],
    phase: ElectionConfigPhase(ConfigAnnouncePhase),
    seq: 0
  }
}

// Can be used to set or remove the ipfs_node any time.
pub fn set_ipfs_node(
  state: ChannelState,
  ipfs_node: Option<IpfsNode>
) -> ChannelState {
  trace @"set_ipfs_node"
  when state is {
    AdminChannel(admin_state) -> AdminChannel(AdminChannelState {
      ..admin_state,
      ipfs_node: ipfs_node,
      seq: admin_state.seq + 1
    })
    SubChannel(sub_state) -> SubChannel(SubChannelState {
      ..sub_state,
      ipfs_node: ipfs_node,
      seq: sub_state.seq + 1
    })
  }
}

// Note that this will work even if it makes an invalid list of subchannels.
// TODO should those checks go here too?
pub fn add_subchannels(
  state: AdminChannelState,
  channels: List<ChannelId>,
  cont_phase: ElectionPhase
) -> AdminChannelState {
  trace @"add_subchannels"
  let cont_channels = list.sort(list.concat(state.subchannels, channels), bytearray.compare)
  trace @"state.channels" : state.subchannels
  trace @"channels"       : channels
  trace @"cont_channels"  : cont_channels
  AdminChannelState(
    state.admin, // should be unchanged
    state.ipfs_node, // should be unchanged
    cont_channels,
    [], // should be reset on each non-post tx
    cont_phase, // TODO should this be validated here rather than separately?
    state.seq + 1 // should be incremented
  )
}

// Note that this doesn't check whether the channels removed make sense.
// TODO should those checks also go here?
pub fn rm_subchannels(
  state: AdminChannelState,
  channels: List<ChannelId>,
  cont_phase: ElectionPhase
) -> AdminChannelState {
  trace @"rm_subchannels"
  AdminChannelState(
    state.admin, // should be unchanged
    state.ipfs_node, // should be unchanged
    remove_elements(state.subchannels, channels),
    [], // should be reset on each non-post tx
    cont_phase, // TODO should this be validated here rather than separately?
    state.seq + 1 // should be incremented
  )
}

// Note that this doesn't check validity of the records or new phase
// TODO should those checks also go here?
pub fn post_public_records(
  state: ChannelState,
  records: List<PublicRecord>,
  cont_phase: Option<ElectionPhase>
) -> ChannelState {
  trace @"post_public_records"
  when state is {
    AdminChannel(admin_state) -> AdminChannel(AdminChannelState(
      admin_state.admin,
      admin_state.ipfs_node,
      admin_state.subchannels,
      records, // should replace the old list
      when cont_phase is {
        Some(phase) -> phase
        None -> admin_state.phase
      },
      admin_state.seq + 1, // should be incremented
    ))
    SubChannel(sub_state) -> SubChannel(SubChannelState(
      sub_state.channel_id,
      sub_state.publisher,
      sub_state.ipfs_node,
      records, // should be replaced
      sub_state.seq + 1, // should be incremented
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

pub fn rebalance_funds_admin(state: AdminChannelState, cont_phase: ElectionPhase) -> AdminChannelState {
  AdminChannelState {
    ..state,
    phase: cont_phase,
    seq: state.seq + 1
  }
}

pub fn rebalance_funds_subchannel(state: SubChannelState) -> SubChannelState {
  SubChannelState {
    ..state,
    seq: state.seq + 1
  }
}
