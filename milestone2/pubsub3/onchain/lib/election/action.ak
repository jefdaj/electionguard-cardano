use election/state.{ChannelId}

// Everyone (including the admin) can do regular actions.
// The admin can also do admin actions.
pub type ElectionAction {
  AdminAct(AdminAction)
  RegularAct(RegularAction)
}

pub type AdminAction {

  // This isn't quite "starting the election", because it can be done
  // before the rest of the config has been figured out. It just creates
  // the admin STT and gives people a policy ID they can refer to.
  InitElection

  // Add one or more subchannels and mint the corresponding STTs.
  AddSubChannels { channels: List<ChannelId> }

  // Remove one or more subchannels and burn the corresponding STTs.
  RmSubChannels { channels: List<ChannelId> }

  // This could probably be done along with RmSubChannels,
  // but I'm keeping them separate for simplicity.
  // Burns the STT and signifies that the election is over.
  // TODO should this require other sigs besides just the admin?
  EndElection

}

pub type RegularAction {

  // Post one or more public records (IPFS CIDs + metadata).
  // Works on either the admin channel or a subchannel.
  PostPublicRecords

}

// TODO remove?
pub fn extract_admin_action(action: ElectionAction) -> Option<AdminAction> {
  when action is {
    AdminAct(admin_act) -> Some(admin_act)
    RegularAct(_) -> None
  }
}
