# Should be kept in sync with onchain/validators/election/types/phase.ak

from pycardano import PlutusData
from dataclasses import dataclass
from typing import Union


# ==================
# ConfigPhase
# ==================

@dataclass
class ConfigAnnouncePhase(PlutusData):
    CONSTR_ID = 0

@dataclass
class ConfigOnboardingPhase(PlutusData):
    CONSTR_ID = 1

@dataclass
class ConfigCeremonyPhase(PlutusData):
    CONSTR_ID = 2

@dataclass
class ConfigFinalizePhase(PlutusData):
    CONSTR_ID = 3

ConfigPhase = Union[
    ConfigAnnouncePhase,
    ConfigOnboardingPhase,
    ConfigCeremonyPhase,
    ConfigFinalizePhase
]


# ==================
# ResultsPhase
# ==================

@dataclass
class ResultsTallyPhase(PlutusData):
    CONSTR_ID = 0

@dataclass
class ResultsDecryptPhase(PlutusData):
    CONSTR_ID = 1

ResultsPhase = Union[ResultsTallyPhase, ResultsDecryptPhase]


# ==================
# ElectionPhase
# ==================

@dataclass
class ElectionConfigPhase(PlutusData):
    CONSTR_ID = 0
    phase: ConfigPhase

    def __repr__(self):
        return f'ElectionConfigPhase({type(self.phase).__name__})'

@dataclass
class ElectionVotingPhase(PlutusData):
    CONSTR_ID = 1

@dataclass
class ElectionResultsPhase(PlutusData):
    CONSTR_ID = 2
    phase: ResultsPhase

    def __repr__(self):
        return f'ElectionResultsPhase({type(self.phase).__name__})'

@dataclass
class ElectionVerifyPhase(PlutusData):
    CONSTR_ID = 3

@dataclass
class ElectionFinalizePhase(PlutusData):
    CONSTR_ID = 4

ElectionPhase = Union[
    ElectionConfigPhase,
    ElectionVotingPhase,
    ElectionResultsPhase,
    ElectionVerifyPhase,
    ElectionFinalizePhase
]
