from __future__ import annotations
import sys
from dataclasses import dataclass, field, asdict
from typing import Mapping, Optional, Self
import hashlib, json
from pathlib import Path
from hypothesis import strategies as st
from copy import deepcopy
# from contextlib import contextmanager
# from hypothesis.strategies import composite, integers, text

from tests.lib.example_data import EXAMPLE_CONTESTS
from tests.lib.json_utils import fancy_dumps, fancy_raw



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

    @classmethod
    def from_dict(cls, data: dict, structure) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data['answers'], dict)
        answers = []
        for k,v in data['answers'].items():
            answers.append((k, structure(v, HashedVotesConfig)))
        return cls(
            question = data['question'],
            answers = tuple(answers)
        )

    def to_dict(self, unstructure) -> dict:
        return {"question": self.question,
                "answers": {k: unstructure(v) for k, v in self.answers}}


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


# @dataclass(frozen=True, slots=True)
# class HashedAdminConfig:
#     template: str = field(default='admin.sh')

# @st.composite
# def hashed_admin_config(draw, template: Optional[str] = None):
#     # TODO remove?
#     _ = draw(st.integers(1,1)) # stop hypothesis complaining about draw
#     kwargs = {}
#     if template is not None:
#         kwargs['template'] = template
#     return HashedAdminConfig(**kwargs)


@dataclass(frozen=True, slots=True)
class HashedGuardiansConfig:
    count: int = 3
    quorum: int = 2
    # template: str = field(default='guardian.sh')

    def __post_init__(self):
        assert 0 < self.quorum <= self.count

@st.composite
def hashed_guardians_config(draw):
    count = draw(st.integers(2,5)) # TODO actual upper bound?
    kwargs = {
        'count':  count,
        'quorum': draw(st.integers(1, count)),
    }
    # if template is not None:
    #     kwargs['template'] = template
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
    # template: str = field(default='device.sh')

@st.composite
def hashed_devices_config(draw):
    kwargs = {
        'count': draw(st.integers(1, 3)), # TODO actual upper bound?
    }
    # if template is not None:
    #     kwargs['template'] = template
    return HashedDevicesConfig(**kwargs)


@dataclass(frozen=True, slots=True)
class HashedVerifiersConfig:
    count: int
    # template: str = field(default='verifier.sh')

@st.composite
def hashed_verifiers_config(draw):
    kwargs = {
        'count': draw(st.integers(1, 3)), # TODO actual upper bound?
    }
    # if template is not None:
    # kwargs['template'] = template
    return HashedVerifiersConfig(**kwargs)

# Used to be called "election", which was confusing
@dataclass(frozen=True, slots=True)
class HashedNodesConfig:
    # admin:     HashedAdminConfig
    guardians: HashedGuardiansConfig
    devices:   HashedDevicesConfig
    verifiers: HashedVerifiersConfig

@st.composite
def hashed_nodes_config(draw):
    return HashedNodesConfig(
        # admin     = draw( hashed_admin_config()     ),
        guardians = draw( hashed_guardians_config() ),
        devices   = draw( hashed_devices_config()   ),
        verifiers = draw( hashed_verifiers_config() ),
    )


@dataclass(frozen=True, slots=True)
class HashedFnCallConfig:
    "A fn call with a name and (kw)args dict."

    name: str
    args: tuple[
        tuple[str, str|int],
        ...
    ]

    @classmethod
    def from_dict(cls, data: dict, structure) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data['args'], dict)
        args = []
        for k,v in data['args'].items():
            args.append((k, structure(v, str|int)))
        return cls(
            name = data['name'],
            args = tuple(args)
        )

    def to_dict(self, unstructure) -> dict:
        # print(f'call cfg to_dict: {self}')
        args = {}
        for a in self.args:
            k, v = a
            args[k] = unstructure(v)
        return {"name": self.name, 'args': args}

    def __post_init__(self):
        assert isinstance(self.args, tuple)
        for pair in self.args:
            assert isinstance(pair, tuple)
            assert len(pair) == 2


@dataclass(frozen=True, slots=True)
class HashedConfigFnsConfig:
    "This one only has names because the fns are strategies."
    names: tuple[str, ...]

    # TODO is this right even though not a dict?
    # def to_dict(self):
    #     return list(self.names)

    def __post_init__(self):
        assert isinstance(self.names, tuple)


@dataclass(frozen=True, slots=True)
class HashedSetupFnsConfig:
    fns: tuple[HashedFnCallConfig, ...]
    def __post_init__(self):
        assert isinstance(self.fns, tuple)

@st.composite
def hashed_setup_fns_config(draw):
    _ = draw(st.integers(1,1)) # silence hypothesis warning
    return HashedSetupFnsConfig(fns=(
        # HashedFnCallConfig.from_dict({
        #     'name': 'render_egc_scripts',
        #     'args': {'default': 'subscribe.sh'}
        # }),
        HashedFnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', 'subscribe.sh'),),
        ),
    ))


@dataclass(frozen=True, slots=True)
class HashedAttackFnsConfig:
    fns: tuple[HashedFnCallConfig, ...]
    def __post_init__(self):
        assert isinstance(self.fns, tuple)

@st.composite
def hashed_attack_fns_config(draw):
    _ = draw(st.integers(1,1)) # silence hypothesis warning
    return HashedAttackFnsConfig(fns=())


@dataclass(frozen=True, slots=True)
class HashedPytestConfig:
    config_fns: HashedConfigFnsConfig
    setup_fns:  HashedSetupFnsConfig
    attack_fns: HashedAttackFnsConfig


@dataclass(frozen=True, slots=True)
class HashedTestConfig:
    pytest: HashedPytestConfig
    arion:  HashedArionConfig
    nodes:  HashedNodesConfig
    votes:  HashedContestsConfig

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
    fn_name = sys._getframe().f_code.co_name # TODO util fn for this
    pytest_config = HashedPytestConfig(
        config_fns = HashedConfigFnsConfig(names=(fn_name,)),
        setup_fns = HashedSetupFnsConfig(fns=(
            # HashedFnCallConfig.from_dict({
            #     'name': 'render_egc_scripts',
            #     'args': {'default': 'subscribe.sh'}
            # }),
            HashedFnCallConfig(
                name = 'render_egc_scripts',
                args = (('default', 'subscribe.sh'),),
            ),
        )),
        attack_fns = HashedAttackFnsConfig(fns=()),
    )
    return HashedTestConfig(
        pytest = pytest_config,
        arion  = draw( hashed_arion_config()    ),
        nodes  = draw( hashed_nodes_config()    ),
        votes  = draw( hashed_contests_config() ),
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

    def cfg_path(self) -> Path:
        return self.tmpdir_path() / 'test.json'

    def lock_path(self) -> Path:
        return self.tmpdir_path() / 'test.lock'

    def log_path(self) -> Path:
        return self.tmpdir_path() / 'test.log'

    def arion_project_name(self):
        return f'egc-test{self.cache_key}'

    def egc_path(self, node_name: str) -> Path:
        assert node_name in self.node_names()
        return self.tmpdir_path() / 'data' / node_name / 'egc'

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

    @classmethod
    def from_hashed_config(cls, cfg: HashedTestConfig, tmp_root: Path) -> Self:
        key = cfg.cache_key()
        return cls(
            config    = cfg,
            cache_key = key,
            tmp_root  = str(tmp_root),
        )

    def to_json(self) -> str:
        cfg = fancy_raw(self.config)
        # print(f'fancy raw cfg: {json.dumps(cfg, indent=2)}')

        # add fields not part of cached config
        cfg['pytest']['cache_key'] = self.cache_key
        cfg['arion']['project_name'] = self.arion_project_name()

        # fix extra nesting
        cfg['pytest']['config_fns'] = cfg['pytest']['config_fns']['names']
        cfg['pytest']['setup_fns' ] = cfg['pytest']['setup_fns' ]['fns']
        cfg['pytest']['attack_fns'] = cfg['pytest']['attack_fns']['fns']
        cfg['votes'] = cfg['votes']['contests']

        # print(f'cfg: {cfg}')
        return fancy_dumps(cfg)

# @contextmanager
def resolve_test_config(cfg: HashedTestConfig, tmp_root: Path) -> ResolvedTestConfig:
    return ResolvedTestConfig.from_hashed_config(cfg, tmp_root)
