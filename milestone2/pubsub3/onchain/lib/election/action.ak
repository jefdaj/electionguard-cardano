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
  // TODO separate into guardian, device, verifier channel lists?
  AddSubChannels { channels: List<ChannelId> }

  // Remove one or more subchannels and burn the corresponding STTs.
  RmSubChannels { channels: List<ChannelId> }

  // Advance to the next election phase.
  // The "only" is because the phase can also be advanced during other
  // operations, which saves transaction costs:
  // - AddSubChannels
  // - RmSubChannesl
  // - PostPublicRecords (admin only)
  // In later iterations, most/all of the phases will probably have specific
  // conditions and transitions can happen automatically once those conditions
  // are met.
  AdvancePhaseOnly

  // Rebalance funds without advancing to the next phase.
  // Makes sure each channel has enough ADA to cover posting fees. Admin can
  // move ADA between channels or add more, but can't remove it from script
  // control. That can only be done at the end of the election.
  // TODO would a list of channel ids help here?
  RebalanceFunds

  // This could probably be done along with RmSubChannels,
  // but I'm keeping them separate for simplicity.
  // Burns the STT and signifies that the election is over.
  // This is the only point where the admin can remove the remaining funds.
  // Later, logic could be added saying they have to go back to a treasury or
  // similar.
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
