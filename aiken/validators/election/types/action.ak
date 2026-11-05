use election/types/channel_id.{ChannelId}

pub type ElectionAction {

  // ===========================================
  // Admin actions spending admin channel
  // ===========================================

  // Admin only, admin channel only.
  // This isn't quite "starting the election", because it can be done
  // before the rest of the config has been figured out. It just creates
  // the admin STT and gives people a policy ID they can refer to.
  // The policy_id makes it easier to find the intial admin STT,
  // and will also be useful for display in the UI.
  // TODO but can we not get policy_id at this point?
  InitElection // { policy_id: PolicyId }

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
  // RmSubChannels, but I'm keeping them separate for simplicity. Burns the admin
  // STT and signifies that the election is over. This is the only point where the
  // admin can remove ADA from the contract. Later, logic could be added saying
  // it must to go back to a treasury or similar.
  EndElection

  // ===========================================
  // Admin actions spending multiple channels
  // ===========================================

  // Admin only, but updates multiple channels.
  // Remove one or more subchannels and burn the corresponding STTs.
  RmSubChannels { channels: List<ChannelId> }

  // Admin only, but updates multiple channels.
  // Makes sure each channel has enough ADA to cover posting fees. Admin can
  // move ADA between channels or add more, but can't remove it from script
  // control. This is almost a no-op from the contract perspective, since that
  // check is run for every action already. But this still needs to update
  // the state of the channels being rebalanced, which can compete with using
  // those same UTXOs to post records. So don't do it more often than needed.
  // Any rebalancing TX must include the admin STT as an input for
  // authorization.
  // TODO expclicit traced check for the admin STT
  RebalanceFunds { channels: List<ChannelId> }

  // ===========================================
  // Single channel actions for anyone
  // ===========================================

  // Set or remove an IPFS node
  // TODO update all python constructors to match this!
  SetIpfsNode

  // Admin or regular publisher, but only one channel.
  // Post a list of one or more public records (IPFS CIDs + metadata).
  // TODO include info to display in UI here? or get from kupo?
  PostPublicRecords

  // Temporary action to ensure that I don't pollute the testnet with
  // unspendable mistakes. Burns any/all STTs, no questions asked.
  BurnTestTokens

}
