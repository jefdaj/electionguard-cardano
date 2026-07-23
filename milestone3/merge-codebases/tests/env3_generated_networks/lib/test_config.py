from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Mapping
import hashlib, json
from hypothesis import strategies as st
from copy import deepcopy
# from hypothesis.strategies import composite, integers, text

from tests.lib.example_data import EXAMPLE_CONTESTS



### hashed test config ###

@dataclass(frozen=True, slots=True)
class HashedVotesConfig:
    """Votes for a particular contest.
    Note that the entire `votes` field in the config is populated by
    HashedContestsConfig; this is only votes for one contest."""

    n_cast: int
    n_spoil: int

@st.composite
def hashed_votes_config(draw) -> HashedVotesConfig:
    return HashedVotesConfig(
        n_cast  = draw(st.integers(0, 3)), # TODO actual bounds?
        n_spoil = draw(st.integers(0, 3)), # TODO actual bounds?
    )


@dataclass(frozen=True, slots=True)
class HashedContestConfig:
    "A single scripted contest with question and vote counts per answer."

    question: str              # office/question
    answers: tuple[
        tuple[
            str,               # candidate/answer
            HashedVotesConfig, # vote counts for candidate/answer
        ],
        ...
    ]

    def to_json(self) -> dict:
        return {"question": self.question,
                "answers": {k: asdict(v) for k, v in self.answers}}


@st.composite
def hashed_contest_config(draw, example) -> HashedContestConfig:
    "A single contest with scripted vote counts for each candidate/answer."
    n_candidates = draw(st.integers(1, len(example['candidates'])))
    example2 = deepcopy(example)
    example2['candidates'] = example2['candidates'][:n_candidates]
    return HashedContestConfig(
        question = example['office'],
        answers = tuple(
            tuple([k, draw(hashed_votes_config())])
            for k in example2['candidates']
        )
    )


@dataclass(frozen=True, slots=True)
class HashedContestsConfig:
    "A list of contests and the scripted vote counts for each one."

    contests: tuple[HashedContestConfig, ...]

    # def to_json(self) -> dict:
    #     return {"question": self.question,
    #             "answers": {k: asdict(v) for k, v in self.answers}}

@st.composite
def hashed_contests_config(draw) -> HashedContestsConfig:
    "A list of unique contests with scripted vote counts for each one."

    contest_idxs = draw(st.lists(
        st.integers(0, len(EXAMPLE_CONTESTS)-1),
        unique=True,
        # max_size=len(EXAMPLE_CONTESTS),
        min_size=1,
        max_size=2, # TODO draw for max
    ))
    # print(f'contest_idxs: {contest_idxs}')
    contests = [
        draw( hashed_contest_config(EXAMPLE_CONTESTS[i]) )
        for i in contest_idxs
    ]
    # print(f'contests: {contests}')
    return HashedContestsConfig(contests=tuple(contests))


@dataclass(frozen=True, slots=True)
class HashedGuardiansConfig:
    count: int = 3
    quorum: int = 2

    def __post_init__(self):
        assert 0 < self.quorum <= self.count

@st.composite
def hashed_guardians_config(draw):
    count = draw(st.integers(2,5)) # TODO actual upper bound?
    return HashedGuardiansConfig(
        count = count,
        quorum = draw(st.integers(1, count)),
    )


# class BindMountsJson(dict):
#     def __init__(self):
#         super(BindMountsJson, self).__init__()
#         self["scripts"] = "/scripts"
#         # self["mockchain"] = "/data/mockchain"
#         self["private"] = "/data/private"
#         # TODO qrcodes

# class HashedArionConfig(dict):
#     def __init__(self):
#         super(HashedArionConfig, self).__init__()
# 
#         # These are derived from the config and will contain the hash, so they
#         # have to be loaded seperately to avoid a circular dependency:
#         # self['project_name'] = 'test'
#         # self['data_dir'] = 'data'
# 
#         # These are different from the old Python egc_scripts. They'll be one
#         # Bash script per container, generated based on the config. Each will
#         # be individually bind mounted into its container.
#         # self['scripts_dir'] = './egc_scripts'
# 
#         # self["private_data"] = "/data/private"
# 
#         # TODO anything else that needs mounting besides private_data?
#         # self['bind_mounts'] = BindMountsJson()

@dataclass(frozen=True, slots=True)
class HashedArionConfig:
    "The parts of the Arion config that should affect the hash."
    egc_image: str
    # TODO add private_dir below
    # TODO add egc_scripts below

@st.composite
def hashed_arion_config(draw):
    _ = draw(st.integers(1,1)) # silence hypothesis warning
    cfg = HashedArionConfig(
        egc_image = "electionguard-cardano:0.3.0",
    )
    return cfg


@dataclass(frozen=True, slots=True)
class HashedDevicesConfig:
    count: int

@st.composite
def hashed_devices_config(draw):
    return HashedDevicesConfig(
        count = draw(st.integers(1, 3)), # TODO actual upper bound?
    )


@dataclass(frozen=True, slots=True)
class HashedVerifiersConfig:
    count: int

@st.composite
def hashed_verifiers_config(draw):
    return HashedVerifiersConfig(
        count = draw(st.integers(1, 3)), # TODO actual upper bound?
    )

# Used to be called "election", which was confusing
@dataclass(frozen=True, slots=True)
class HashedNodesConfig:
    guardians: HashedGuardiansConfig
    devices:   HashedDevicesConfig
    verifiers: HashedVerifiersConfig

@st.composite
def hashed_nodes_config(draw):
    return HashedNodesConfig(
        guardians = draw( hashed_guardians_config() ),
        devices   = draw( hashed_devices_config()   ),
        verifiers = draw( hashed_verifiers_config() ),
    )

@dataclass(frozen=True, slots=True)
class HashedAttacksConfig:
    attacks: tuple[str, ...]

@st.composite
def hashed_attacks_config(draw):
    _ = draw(st.integers(1,1)) # silence hypothesis warning
    return HashedAttacksConfig(attacks=()) # TODO write this


@dataclass(frozen=True, slots=True)
class HashedTestConfig:
    arion:   HashedArionConfig
    nodes:   HashedNodesConfig
    votes:   HashedContestsConfig # TODO rename contests?
    attacks: HashedAttacksConfig

    def canonical(self) -> str:
        # sort_keys canonicalizes DICT KEYS only; list/tuple order is untouched
        return json.dumps(asdict(self), sort_keys=True,
                           separators=(",", ":"), default=str)

    def cache_key(self) -> str:
        # TODO any reason sha256 is better than md5 here?
        # return hashlib.md5(self.canonical().encode()).hexdigest()[:5]
        return hashlib.sha256(self.canonical().encode()).hexdigest()[:8]

@st.composite
def hashed_test_config(draw) -> HashedTestConfig:
    return HashedTestConfig(
        arion    = draw( hashed_arion_config()    ),
        nodes    = draw( hashed_nodes_config()    ),
        votes    = draw( hashed_contests_config() ), # TODO rename contests?
        attacks  = draw( hashed_attacks_config()  ),
    )


### resolved test config ###

@dataclass(frozen=True, slots=True)
class ResolvedTestConfig:
    """Final test config including the non-hashed parts. Since this doesn't
    need to be round-tripped, some things are just in the JSON output."""

    config: HashedTestConfig
    cache_key: str

    def tmpdir_path(self, tmp_root: Path):
        return tmp_root / f'test{self.cache_key}'

    def arion_project_name(self):
        return f'egc-test-{self.cache_key}'

    @classmethod
    def from_hashed_config(cls, cfg: HashedTestConfig) -> Self:
        key = cfg.cache_key()
        return cls(
            config    = cfg,
            cache_key = key,
        )

    def to_json(self) -> dict:
        return json.dumps(asdict(self), indent=2) # TODO sort_keys=True?
