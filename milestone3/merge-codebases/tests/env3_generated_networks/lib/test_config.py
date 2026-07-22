from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Mapping
import hashlib, json
from hypothesis.strategies import composite, integers, text


### hashed test config ###

@dataclass(frozen=True, slots=True)
class HashedVotesConfig:
    n_cast: int
    n_spoil: int

@composite
def hashed_votes_config(draw) -> HashedVotesConfig:
    return HashedVotesConfig(
        n_cast  = draw(integers(0, 3)), # TODO actual bounds?
        n_spoil = draw(integers(0, 3)), # TODO actual bounds?
    )


# TODO static list of actual example contests to draw from here

@dataclass(frozen=True, slots=True)
class HashedContestsConfig:
    "One contest in the list under `votes`"
    question: str
    answers: tuple[tuple[str, HashedVotesConfig], ...]

    def to_json(self) -> dict:
        return {"question": self.question,
                "answers": {k: asdict(v) for k, v in self.answers}}

@composite
def hashed_contests_config(draw) -> HashedContestsConfig:
    n = draw(integers(1, 5))
    answers = tuple(
        # TODO what do these look like?
        (draw(text(min_size=1, max_size=8)), draw(hashed_votes_config()))
        for _ in range(n)
    )
    return HashedContestsConfig(question=draw(text(min_size=1)), answers=answers)


@dataclass(frozen=True, slots=True)
class HashedGuardiansConfig:
    count: int = 3
    quorum: int = 2

    def __post_init__(self):
        assert 0 < self.quorum <= self.count

@composite
def hashed_guardians_config(draw):
    count = draw(integers(2,5)) # TODO actual upper bound?
    return HashedGuardiansConfig(
        count = count,
        quorum = draw(integers(1, count)),
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

@composite
def hashed_arion_config(draw):
    _ = draw(integers(1,1)) # silence hypothesis warning
    cfg = HashedArionConfig(
        egc_image = "electionguard-cardano:0.3.0",
    )
    return cfg


@dataclass(frozen=True, slots=True)
class HashedDevicesConfig:
    count: int

@composite
def hashed_devices_config(draw):
    return HashedDevicesConfig(
        count = draw(integers(1, 3)), # TODO actual upper bound?
    )


@dataclass(frozen=True, slots=True)
class HashedVerifiersConfig:
    count: int

@composite
def hashed_verifiers_config(draw):
    return HashedVerifiersConfig(
        count = draw(integers(1, 3)), # TODO actual upper bound?
    )

# Used to be called "election", which was confusing
@dataclass(frozen=True, slots=True)
class HashedNodesConfig:
    guardians: HashedGuardiansConfig
    devices:   HashedDevicesConfig
    verifiers: HashedVerifiersConfig

@composite
def hashed_nodes_config(draw):
    return HashedNodesConfig(
        guardians = draw( hashed_guardians_config() ),
        devices   = draw( hashed_devices_config()   ),
        verifiers = draw( hashed_verifiers_config() ),
    )

@dataclass(frozen=True, slots=True)
class HashedAttacksConfig:
    attacks: tuple[str, ...]

@composite
def hashed_attacks_config(draw):
    _ = draw(integers(1,1)) # silence hypothesis warning
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
        return hashlib.sha256(self.canonical().encode()).hexdigest()[:16]

@composite
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
    "Final test config including the non-hashed parts."

    config:      HashedTestConfig
    tmpdir:      str
    docker_name: str

    @classmethod
    def from_hashed_config(cls, cfg: HashedTestConfig, tmp_root: Path) -> Self:
        key = cfg.cache_key()
        return cls(
            config      = cfg,
            tmpdir      = str(tmp_root / f'test{key}'),
            docker_name = f'egc-test{key}',
        )
