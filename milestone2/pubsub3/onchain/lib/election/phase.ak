// For now, this is simplified by assuming that we don't need to go back and
// edit earlier phases of the election. So for example once we're in the
// ballots phase we don't need to keep posting the config.
pub type ElectionPhase {
  ElectionConfigPhase(ConfigPhase)
  ElectionBallotsPhase
  ElectionResultsPhase(ResultsPhase)
  ElectionVerifyPhase
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

// TODO in InitElection and EndElection, check for initial + final phases respectively
pub fn is_valid_phase_transition(old: ElectionPhase, new: ElectionPhase) -> Bool {
  when old is {
    ElectionConfigPhase(ConfigAnnouncePhase)  -> new == ElectionConfigPhase(ConfigChannelsPhase)
    ElectionConfigPhase(ConfigChannelsPhase)  -> new == ElectionConfigPhase(ConfigCeremonyPhase)
    ElectionConfigPhase(ConfigCeremonyPhase)  -> new == ElectionConfigPhase(ConfigFinalizePhase)
    ElectionConfigPhase(ConfigFinalizePhase)  -> new == ElectionBallotsPhase
    ElectionBallotsPhase                      -> new == ElectionResultsPhase(ResultsTallyPhase)
    ElectionResultsPhase(ResultsTallyPhase)   -> new == ElectionResultsPhase(ResultsDecryptPhase)
    ElectionResultsPhase(ResultsDecryptPhase) -> new == ElectionResultsPhase(ResultsSummaryPhase)
    ElectionResultsPhase(ResultsSummaryPhase) -> new == ElectionVerifyPhase
    ElectionVerifyPhase -> False
  }
}
