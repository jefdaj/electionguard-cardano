// For now, this is simplified by assuming that we don't need to go back and
// edit earlier phases of the election. So for example once we're in the
// ballots phase we don't need to keep posting the config.
pub type ElectionPhase {
  ElectionConfigPhase(ConfigPhase)
  ElectionBallotsPhase
  ElectionResultsPhase(ResultsPhase)
  ElectionVerifyPhase
}

pub type ConfigPhase {
  ConfigAnnouncePhase
  ConfigCeremonyPhase
  ConfigFinalizePhase // TODO is that a good name?
  ConfigDevicesPhase
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
  ResultsSummaryPhase
}
