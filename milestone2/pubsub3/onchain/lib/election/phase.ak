// For now, this is simplified by assuming that we don't need to go back and
// edit earlier phases of the election. So for example once we're in the
// ballots phase we don't need to keep posting the config.
pub type ElectionPhase {
  ElectionConfigPhase(ConfigPhase)
  ElectionBallotsPhase
  ElectionResultsPhase(ResultsPhase)
  ElectionVerifyPhase
  ElectionFinalizePhase // TODO adjust electionguard code to add this
}

// TODO adjust electionguard code to reflect ConfigChannelsPhase idea
pub type ConfigPhase {
  ConfigAnnouncePhase
  ConfigChannelsPhase // mint all channels + announce devices
  ConfigCeremonyPhase
  ConfigFinalizePhase // TODO adjust electionguard code to refer to 3_election this way
}

// TODO any reason to add detail about these?
// pub type CeremonyRound {
//   CeremonyRound1
//   CeremonyRound2
//   CeremonyRound3
// }

pub type ResultsPhase {
  ResultsTallyPhase
  ResultsDecryptPhase
  ResultsSummaryPhase // TODO remove as redundant with ElectionVerifyPhase?
}

pub fn is_initial_phase(phase: ElectionPhase) -> Bool {
  phase == ElectionConfigPhase(ConfigAnnouncePhase)
}

pub fn is_final_phase(phase: ElectionPhase) -> Bool {
  phase == ElectionFinalizePhase
}

// TODO in InitElection and EndElection, check for initial + final phases respectively
pub fn is_valid_phase_transition(old: ElectionPhase, new: ElectionPhase) -> Bool {
  when old is {
    ElectionConfigPhase(ConfigAnnouncePhase)  -> new == old || new == ElectionConfigPhase(ConfigChannelsPhase)
    ElectionConfigPhase(ConfigChannelsPhase)  -> new == old || new == ElectionConfigPhase(ConfigCeremonyPhase)
    ElectionConfigPhase(ConfigCeremonyPhase)  -> new == old || new == ElectionConfigPhase(ConfigFinalizePhase)
    ElectionConfigPhase(ConfigFinalizePhase)  -> new == old || new == ElectionBallotsPhase
    ElectionBallotsPhase                      -> new == old || new == ElectionResultsPhase(ResultsTallyPhase)
    ElectionResultsPhase(ResultsTallyPhase)   -> new == old || new == ElectionResultsPhase(ResultsDecryptPhase)
    ElectionResultsPhase(ResultsDecryptPhase) -> new == old || new == ElectionResultsPhase(ResultsSummaryPhase)
    ElectionResultsPhase(ResultsSummaryPhase) -> new == old || new == ElectionVerifyPhase
    ElectionVerifyPhase                       -> new == old || new == ElectionFinalizePhase
    ElectionFinalizePhase                     -> False
  }
}
