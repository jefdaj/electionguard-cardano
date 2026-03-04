pub type ElectionAction {
  AdminAction(AdminAction)
  SubChannelAction(SubChannelAction)
}

pub type AdminAction {

  /// Open the channel, minting the STT and funding with min ADA.
  // TODO also send extra ADA to pay publishing fees?
  AdminOpenChannel

  // TODO ForkSubChannel

  /// Announce publication of some new_records.
  AdminPostPublicRecords

  // Collect ADA and/or other tokens sent to the validator.
  // TODO sending ADA to the contract is always valid, right?
  // Collect

  // TODO JoinSubChannel? (or is that handled by CloseChannel?)

  /// Close the channel, burning the STT and recovering any ADA.
  /// The publisher can choose whether to collect other tokens here too.
  // TODO if not, are they basically burned/frozen at the validator address?
  // TODO should it require exlicitly burning any assets you don't want?
  AdminCloseChannel

}

pub type SubChannelAction {
  SubChannelPostPublicRecords
}
