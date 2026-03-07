use election/state.{ChannelId}

pub type ElectionAction {

  // ===========================================
  // Admin actions spending admin channel
  // ===========================================

  // Admin only, admin channel only.
  // This isn't quite "starting the election", because it can be done
  // before the rest of the config has been figured out. It just creates
  // the admin STT and gives people a policy ID they can refer to.
  InitElection

  // Admin only, admin channel only (because the new subchannel STTs aren't
  // being spent). Add one or more subchannels and mint the corresponding STTs.
  // TODO separate into guardian, device, verifier channel lists?
  AddSubChannels { channels: List<ChannelId> }

  // Admin only, admin channel only. Advance to the next election phase. The
  // phase can also be advanced during other actions to save on fees and
  // confirmation time:
  // - AddSubChannels
  // - RmSubChannels
  // - RebalanceFunds
  // - PostPublicRecords (to admin channel)
  // In later iterations, many/all of the phases will probably have custom
  // logic for when they can be advanced.
  AdvancePhase

  // Admin only, admin channel only. This could probably be done along with
  // RmSubChannels, but I'm keeping them separate for simplicity. Burns the STT
  // and signifies that the election is over. This is the only point where the
  // admin can remove the remaining funds. Later, logic could be added saying
  // they have to go back to a treasury or similar.
  EndElection

  // ===========================================
  // Admin actions spending multiple channels
  // ===========================================

  // Admin only, but touches multiple channels.
  // Remove one or more subchannels and burn the corresponding STTs.
  RmSubChannels { channels: List<ChannelId> }

  // Admin only, but touches multiple channels.
  // Makes sure each channel has enough ADA to cover posting fees. Admin can
  // move ADA between channels or add more, but can't remove it from script
  // control. This is almost a no-op from the contract perspective, since that
  // check is run for every action already. Note that it still has to update
  // the state of the channels being rebalanced, which can compete with using
  // those same UTXOs to post records. So don't do it more often than needed.
  RebalanceFunds { channels: List<ChannelId> }

  // ===========================================
  // Single channel actions for anyone
  // ===========================================

  // Admin or regular publisher, but only one channel.
  // Post one or more public records (IPFS CIDs + metadata).
  // Works on either the admin channel or a subchannel.
  PostPublicRecords

}
