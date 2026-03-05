pub type ElectionAction {
  AdminAct(AdminAction)
  RegularAct(RegularAction)
}

pub type AdminAction {
  InitElection
  EndElection
}

pub type RegularAction {
  PostPublicRecords
}

// TODO remove?
pub fn extract_admin_action(action: ElectionAction) -> Option<AdminAction> {
  when action is {
    AdminAct(admin_act) -> Some(admin_act)
    RegularAct(_) -> None
  }
}
