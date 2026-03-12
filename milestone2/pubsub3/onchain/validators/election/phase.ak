// For now, this is simplified by assuming that we don't need to go back and
// edit earlier phases of the election. So for example once we're in the
// ballots phase we don't need to keep posting the config.
pub type ElectionPhase {

  // Everything needed to set up the election before voting can begin.
  ElectionConfigPhase(ConfigPhase)

  // All ballot artifacts are posted in this phase: submitted, cast, spoiled.
  // In the future this could also be used to gate the voting start time.
  ElectionVotingPhase // TODO rename ballots -> voting in electionguard code

  // At this point voting is finished and the guardians + admin can decrypt the
  // final tally + spoiled ballots. In the future this could also be used to
  // gate the voting end time.
  // TODO would it be a good idea for this to optionally happen in parallel with voting?
  ElectionResultsPhase(ResultsPhase)

  // This is where official verifiers (and in the future unofficial ones too)
  // post their verification summaries.
  // TODO is this redundant with ResultsSummaryPhase?
  ElectionVerifyPhase

  // This is where the admin closes all subchannels and recovers their remaining ADA.
  // In the future it could also be used to signify that the election is officially over
  // (all disputes and verifications have been resolved).
  ElectionFinalizePhase // TODO adjust electionguard code to add this

}

// TODO adjust electionguard code to reflect ConfigOnboardingPhase idea
pub type ConfigPhase {

  // The admin STT is created here, and the admin posts the manifest + guardian details.
  // TODO should the guardian details be mutable and/or later, after onboarding?
  // TODO should the admin announce an expected number of devices here too for consistency?
  ConfigAnnouncePhase

  // This is where anyone who needs a channel (guardians, devices) sends the
  // admin their wallet address. The admin confirms by minting a channel STT
  // with their VerificationKeyHash and by sending them some ADA to cover
  // collateral when posting.
  ConfigOnboardingPhase

  // Guardian key ceremony in 3 rounds:
  // 1. post your public key
  // 2. send secret shares of your private key to other guardians
  // 3. verify that you recieved their secret shares
  ConfigCeremonyPhase

  // Admin posts the final cryptographic settings for the election,
  // including the joint public key.
  ConfigFinalizePhase // TODO adjust electionguard code to refer to 3_election this way

}

// TODO any reason to add detail about these?
// pub type CeremonyRound {
//   CeremonyRound1
//   CeremonyRound2
//   CeremonyRound3
// }

pub type ResultsPhase {

  // Admin posts an encrypted final tally.
  ResultsTallyPhase

  // Guardians post decryption shares for the tally + each individual spoiled ballot,
  // then the admin combines them and posts the final decrypted versions.
  // TODO should that be two separate phases?
  ResultsDecryptPhase

  // ResultsSummaryPhase // TODO remove as redundant with ElectionVerifyPhase?

}

pub fn is_initial_phase(phase: ElectionPhase) -> Bool {
  phase == ElectionConfigPhase(ConfigAnnouncePhase)
}

pub fn is_final_phase(phase: ElectionPhase) -> Bool {
  phase == ElectionFinalizePhase
}

pub fn is_valid_phase_transition(old: ElectionPhase, new: ElectionPhase) -> Bool {
  old == new || is_valid_phase_advance(old, new)
}

fn is_valid_phase_advance(old: ElectionPhase, new: ElectionPhase) -> Bool {
  when old is {
    ElectionConfigPhase(ConfigAnnouncePhase)   -> new == ElectionConfigPhase(ConfigOnboardingPhase)
    ElectionConfigPhase(ConfigOnboardingPhase) -> new == ElectionConfigPhase(ConfigCeremonyPhase)
    ElectionConfigPhase(ConfigCeremonyPhase)   ->
      // TODO remove ConfigFinalizePhase if it's not really needed?
      new == ElectionConfigPhase(ConfigFinalizePhase) || new == ElectionVotingPhase
    ElectionConfigPhase(ConfigFinalizePhase)   -> new == ElectionVotingPhase
    ElectionVotingPhase                        -> new == ElectionResultsPhase(ResultsTallyPhase)
    ElectionResultsPhase(ResultsTallyPhase)    -> new == ElectionResultsPhase(ResultsDecryptPhase)
    ElectionResultsPhase(ResultsDecryptPhase)  -> new == ElectionVerifyPhase
    ElectionVerifyPhase                        -> new == ElectionFinalizePhase
    ElectionFinalizePhase                      -> False
  }
}
