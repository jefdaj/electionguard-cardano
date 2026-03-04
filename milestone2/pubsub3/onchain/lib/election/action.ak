pub type ElectionAction {
  AdminAct(AdminAction)
  RegularAct(RegularAction)
}

pub type AdminAction {
  OpenChannel  // TODO rename OpenElection?
  CloseChannel // TODO rename CloseElection?
}

pub type RegularAction {
  PostPublicRecords
}

// TODO remove?
pub fn extract_admin_action(action: ElectionAction) -> Option<AdminAction> {
  when action is {
    AdminAct(admin_action) -> Some(admin_action)
    RegularAct(_) -> None
  }
}
