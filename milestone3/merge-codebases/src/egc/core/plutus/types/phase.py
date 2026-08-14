# Should be kept in sync with onchain/validators/election/types/phase.ak

from pycardano import PlutusData
from dataclasses import dataclass
from typing import Union, get_args
from functools import total_ordering


@total_ordering
class OrderedPhase(PlutusData):
    "Mixin for phase comparison using _phase_key (defined below)."

    def __eq__(self, other):
        if not isinstance(other, OrderedPhase):
            raise NotImplementedError
        return _phase_key(self) == _phase_key(other)

    def __lt__(self, other):
        if not isinstance(other, OrderedPhase):
            raise NotImplementedError
        return _phase_key(self) < _phase_key(other)

    def __hash__(self):
        return hash((type(self), _phase_key(self)))


# ==================
# ConfigPhase
# ==================

@dataclass(eq=False)
class ConfigAnnouncePhase(OrderedPhase):
    CONSTR_ID = 0

@dataclass(eq=False)
class ConfigOnboardingPhase(OrderedPhase):
    CONSTR_ID = 1

@dataclass(eq=False)
class ConfigCeremonyPhase(OrderedPhase):
    CONSTR_ID = 2

@dataclass(eq=False)
class ConfigFinalizePhase(OrderedPhase):
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

@dataclass(eq=False)
class ResultsTallyPhase(OrderedPhase):
    CONSTR_ID = 0

@dataclass(eq=False)
class ResultsDecryptPhase(OrderedPhase):
    CONSTR_ID = 1

ResultsPhase = Union[ResultsTallyPhase, ResultsDecryptPhase]


# ==================
# ElectionPhase
# ==================

@dataclass(eq=False)
class ElectionConfigPhase(OrderedPhase):
    CONSTR_ID = 0
    phase: ConfigPhase

@dataclass(eq=False)
class ElectionVotingPhase(OrderedPhase):
    CONSTR_ID = 1

@dataclass(eq=False)
class ElectionResultsPhase(OrderedPhase):
    CONSTR_ID = 2
    phase: ResultsPhase

@dataclass(eq=False)
class ElectionVerifyPhase(OrderedPhase):
    CONSTR_ID = 3

@dataclass(eq=False)
class ElectionFinalizePhase(OrderedPhase):
    CONSTR_ID = 4

ElectionPhase = Union[
    ElectionConfigPhase,
    ElectionVotingPhase,
    ElectionResultsPhase,
    ElectionVerifyPhase,
    ElectionFinalizePhase
]

def _phase_key(obj):
    "Key for comparing OrderedPhase objects."
    for i, union in enumerate([ConfigPhase, ResultsPhase, ElectionPhase]):
        members = get_args(union)
        if type(obj) in members:
            rank = (i, members.index(type(obj)))
            sub = getattr(obj, "phase", None)
            return (rank, _phase_key(sub)) if sub is not None else (rank, ())
    raise TypeError(f"{type(obj)} is not a registered phase")
