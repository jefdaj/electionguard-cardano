from enum import Enum
from typing import Optional
from functools import total_ordering
from .plutus.types.phase import *
import logging


LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class EgcPhaseContext:
    "Extra context needed to determine EgcPhase from (on-chain) ElectionPhase."

    # TODO add key ceremony rounds: 1,2,3
    # TODO add transition grace periods that finish when everyone announces they're ready

    # Whether the Kupo thread has started indexing yet.
    indexed: bool

    # Disambiguates whether an onchain_phase of None means before or after election.
    deployed: bool

    # Tracks progress of the key ceremony. We could add explicit sub-phases for
    # the rounds, but then the admin would need to advance them. This way the
    # guardians can determine everything themselves and theoretically complete
    # the whole ceremony within 3 blocks.
    ceremony_round1_complete: bool
    ceremony_round2_complete: bool

    onchain_phase: Optional[ElectionPhase]


@total_ordering
class EgcPhase(Enum):
    """A more complete phase that includes on-chain ElectionPhase + other info.
    It should be preferred over raw ElectionPhase for use in interfaces etc.
    """

    # TODO should there also be a catchall "error" phase in case of invalid state?

    NOT_INDEXED            = 0 # no election subscribed to, or Kupo starting up
    NOT_DEPLOYED           = 1 # init_election not run yet, or tx not confirmed
    CONFIG_ANNOUNCE        = 2
    CONFIG_ONBOARDING      = 3
    CONFIG_CEREMONY_ROUND1 = 4
    CONFIG_CEREMONY_ROUND2 = 5
    CONFIG_CEREMONY_ROUND3 = 6
    CONFIG_FINALIZE        = 7
    VOTING                 = 8
    RESULTS_TALLY          = 9
    RESULTS_DECRYPT        = 10
    VERIFY                 = 11
    FINALIZE               = 12
    FINISHED               = 13

    def __lt__(self, other):
        if not isinstance(other, EgcPhase):
            return NotImplemented
        return self.value < other.value


def resolve_egc_phase(ctx: EgcPhaseContext) -> EgcPhase:
    if not ctx.indexed:
        return EgcPhase.NOT_INDEXED
    if ctx.onchain_phase is None:
        return EgcPhase.FINISHED if ctx.deployed else EgcPhase.NOT_DEPLOYED
    match ctx.onchain_phase:
        case ElectionConfigPhase(phase=p):
            match p:
                case ConfigAnnouncePhase():   return EgcPhase.CONFIG_ANNOUNCE
                case ConfigOnboardingPhase(): return EgcPhase.CONFIG_ONBOARDING
                case ConfigCeremonyPhase():
                    if not ctx.ceremony_round1_complete:
                        return EgcPhase.CONFIG_CEREMONY_ROUND1
                    elif not ctx.ceremony_round2_complete:
                        return EgcPhase.CONFIG_CEREMONY_ROUND2
                    else:
                        return EgcPhase.CONFIG_CEREMONY_ROUND3
                case ConfigFinalizePhase():   return EgcPhase.CONFIG_FINALIZE
                case _: assert_never(p)
        case ElectionVotingPhase(): return EgcPhase.VOTING
        case ElectionResultsPhase(phase=p):
            match p:
                case ResultsTallyPhase():   return EgcPhase.RESULTS_TALLY
                case ResultsDecryptPhase(): return EgcPhase.RESULTS_DECRYPT
                case _: assert_never(p)
        case ElectionVerifyPhase():   return EgcPhase.VERIFY
        case ElectionFinalizePhase(): return EgcPhase.FINALIZE
        case _: assert_never(ctx.onchain_phase)


def resolve_onchain_phase(egc_phase: EgcPhase) -> Optional[ElectionPhase]:
    "Used by `egc phase advance` to translate to internal (on-chain) type."
    # TODO is there a better/clever way?
    match egc_phase.value:
        case 0:  return None
        case 1:  return None
        case 2:  return ElectionConfigPhase(ConfigAnnouncePhase())
        case 3:  return ElectionConfigPhase(ConfigOnboardingPhase())
        case 4:  return ElectionConfigPhase(ConfigCeremonyPhase())
        case 5:  return ElectionConfigPhase(ConfigCeremonyPhase())
        case 6:  return ElectionConfigPhase(ConfigCeremonyPhase())
        case 7:  return ElectionConfigPhase(ConfigFinalizePhase())
        case 8:  return ElectionVotingPhase()
        case 9:  return ElectionResultsPhase(ResultsTallyPhase())
        case 10: return ElectionResultsPhase(ResultsDecryptPhase())
        case 11: return ElectionVerifyPhase()
        case 12: return ElectionFinalizePhase()
        case 13: return None
        case _:  raise NotImplementedError
