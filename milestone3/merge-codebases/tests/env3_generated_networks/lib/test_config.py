from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Mapping, Optional
import hashlib, json
from pathlib import Path
from hypothesis import strategies as st
from copy import deepcopy
# from contextlib import contextmanager
# from hypothesis.strategies import composite, integers, text

from tests.lib.example_data import EXAMPLE_CONTESTS
from tests.lib.json_utils import fancy_dumps



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

    def to_dict(self) -> dict:
        return {"question": self.question,
                "answers": {k: asdict(v) for k, v in self.answers}}


@st.composite
def hashed_contest_config(draw, example) -> HashedContestConfig:
    "A single contest with scripted vote counts for each candidate/answer."
    n_candidates = draw(st.integers(2, len(example['candidates']))) # TODO allow one candidate?
    example2 = deepcopy(example)
    example2['candidates'] = example2['candidates'][:n_candidates]
    return HashedContestConfig(
        question = example['office'],
        answers = tuple(
            tuple([k, draw(hashed_votes_config())])
            for k in example2['candidates']
        )
    )
    # TODO assume at least one vote here?


@dataclass(frozen=True, slots=True)
class HashedContestsConfig:
    "A list of contests and the scripted vote counts for each one."

    contests: tuple[HashedContestConfig, ...]

    # def to_dict(self) -> dict:
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
        max_size=1, # TODO draw for max
    ))
    # print(f'contest_idxs: {contest_idxs}')
    contests = [
        draw( hashed_contest_config(EXAMPLE_CONTESTS[i]) )
        for i in contest_idxs
    ]
    # print(f'contests: {contests}')
    return HashedContestsConfig(contests=tuple(contests))


@dataclass(frozen=True, slots=True)
class HashedAdminConfig:
    egc_template: str = field(default='admin.sh')

@st.composite
def hashed_admin_config(draw, egc_template: Optional[str] = None):
    # TODO remove?
    _ = draw(st.integers(1,1)) # stop hypothesis complaining about draw
    kwargs = {}
    if egc_template is not None:
        kwargs['egc_template'] = egc_template
    return HashedAdminConfig(**kwargs)


@dataclass(frozen=True, slots=True)
class HashedGuardiansConfig:
    count: int = 3
    quorum: int = 2
    egc_template: str = field(default='guardian.sh')

    def __post_init__(self):
        assert 0 < self.quorum <= self.count

@st.composite
def hashed_guardians_config(draw, egc_template: Optional[str] = None):
    count = draw(st.integers(2,5)) # TODO actual upper bound?
    kwargs = {
        'count':  count,
        'quorum': draw(st.integers(1, count)),
    }
    if egc_template is not None:
        kwargs['egc_template'] = egc_template
    return HashedGuardiansConfig(**kwargs)


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
    egc_template: str = field(default='device.sh')

@st.composite
def hashed_devices_config(draw, egc_template: Optional[str] = None):
    kwargs = {
        'count': draw(st.integers(1, 3)), # TODO actual upper bound?
    }
    if egc_template is not None:
        kwargs['egc_template'] = egc_template
    return HashedDevicesConfig(**kwargs)


@dataclass(frozen=True, slots=True)
class HashedVerifiersConfig:
    count: int
    egc_template: str = field(default='verifier.sh')

@st.composite
def hashed_verifiers_config(draw, egc_template: Optional[str] = None):
    kwargs = {
        'count': draw(st.integers(1, 3)), # TODO actual upper bound?
    }
    if egc_template is not None:
        kwargs['egc_template'] = egc_template
    return HashedVerifiersConfig(**kwargs)

# Used to be called "election", which was confusing
@dataclass(frozen=True, slots=True)
class HashedNodesConfig:
    admin:     HashedAdminConfig
    guardians: HashedGuardiansConfig
    devices:   HashedDevicesConfig
    verifiers: HashedVerifiersConfig

@st.composite
def hashed_nodes_config(draw):
    return HashedNodesConfig(
        admin     = draw( hashed_admin_config()     ),
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
        return hashlib.sha256(self.canonical().encode()).hexdigest()[:5]

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
    tmp_root: Path

    def tmpdir_path(self) -> Path:
        return Path(self.tmp_root) / f'test{self.cache_key}'

    def arion_project_name(self):
        return f'egc-test{self.cache_key}'

    def node_names(self):
        names  = ['admin']
        names += [f'guardian{n}' for n in range(1, self.config.nodes.guardians.count+1)]
        names += [  f'device{n}' for n in range(1,   self.config.nodes.devices.count+1)]
        names += [f'verifier{n}' for n in range(1, self.config.nodes.verifiers.count+1)]
        return names

    def bind_dirs(self) -> list[Path]:
        "Dirs that should be created with user permissions before `arion up`."
        per_node_dirs = [
            'ipfs',
            'egc',
            # TODO what else?
        ]
        dirs = []
        for name in self.node_names():
            dirs += [f'data/{name}/{d}' for d in per_node_dirs]
        return sorted(list(dirs))

    def egc_scripts(self) -> list[Path]:
        # TODO one per node rather than one per node type?
        return {
            'admin':    self.admin.egc_template,
            'guardian': self.guardians.egc_template,
            'device':   self.devices.egc_template,
            'verifier': self.verifiers.egc_template,
        }

    @classmethod
    def from_hashed_config(cls, cfg: HashedTestConfig, tmp_root: Path) -> Self:
        key = cfg.cache_key()
        return cls(
            config    = cfg,
            cache_key = key,
            tmp_root  = str(tmp_root),
        )

    def to_json(self) -> str:
        cfg = asdict(self.config)
        cfg['tmpdir_path'] = str(self.tmpdir_path())
        cfg['arion']['project_name'] = self.arion_project_name()
        # print(f'cfg: {cfg}')
        cfg['bind_dirs'] = [str(d) for d in self.bind_dirs()]
        cfg['scripts'] = self.egc_scripts()
        # print(f'cfg bind_dirs: {cfg['bind_dirs']}')

        # fix answers being converted to short lists rather than dicts,
        # and accidental nesting of contests in votes
        tmp = cfg['votes']['contests']
        cfg['votes'] = []
        for contest in tmp:
            c = {'question': contest['question'], 'answers': {}}
            for k, v in contest['answers']:
                c['answers'][k] = v
            cfg['votes'].append(c)

        # fix accidental nesting of attacks in attacks
        cfg['attacks'] = cfg['attacks']['attacks']

        # print(f'cfg: {cfg}')
        return fancy_dumps(cfg)

# @contextmanager
def resolve_test_config(cfg: HashedTestConfig, tmp_root: Path) -> ResolvedTestConfig:
    return ResolvedTestConfig.from_hashed_config(cfg, tmp_root)
