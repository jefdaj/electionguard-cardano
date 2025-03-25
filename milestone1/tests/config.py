#!/usr/bin/env python3

import json
import os

from hypothesis import given, settings, assume
from hypothesis.strategies import integers, composite
from typing import Callable, Dict


### config classes ###

class BindMountsConfig(dict):
    def __init__(self):
        super(BindMountsConfig, self).__init__()
        self["scripts"] = "/scripts"
        self["public" ] = "/data/public"
        self["private"] = "/data/private"

class ArionConfig(dict):
    def __init__(self):
        super(ArionConfig, self).__init__()
        self['project_name'] = 'test'
        self['data_dir'] = 'data'
        self['bind_mounts'] = BindMountsConfig()

class VoteConfig(dict):
    def __init__(self, n_cast: int, n_spoil: int):
        super(VoteConfig, self).__init__()
        assert n_cast  >= 0
        assert n_spoil >= 0
        self['cast' ] = n_cast
        self['spoil'] = n_spoil

class ContestConfig(dict):
    "One contest in the list under `votes`"
    # TODO less confusing names
    def __init__(self, question: str, answers: Dict[str, VoteConfig]):
        super(ContestConfig, self).__init__()
        self['question'] = question
        self['answers' ] = answers

class GuardiansConfig(dict):
    def __init__(self, count: int = 3, quorum: int = 2):
        super(GuardiansConfig, self).__init__()
        assert quorum > 0
        assert quorum <= count
        self['count' ] = count
        self['quorum'] = quorum

class DevicesConfig(dict):
    def __init__(self, count: int = 4):
        super(DevicesConfig, self).__init__()
        assert count >= 1
        self['count'] = count

class VerifiersConfig(dict):
    def __init__(self, count: int = 2):
        super(VerifiersConfig, self).__init__()
        self['count'] = count

class ElectionConfig(dict):
    def __init__(self,
        guardians_count  : int = 3,
        guardians_quorum : int = 2,
        devices_count    : int = 3,
        verifiers_count  : int = 2,
    ):
        super(ElectionConfig, self).__init__()
        self['guardians'] = GuardiansConfig(guardians_count, guardians_quorum)
        self['devices'  ] = DevicesConfig(devices_count)
        self['verifiers'] = VerifiersConfig(verifiers_count)

class ProjectConfig(dict):
    def __init__(self, arion_cfg, election_cfg, votes_cfg):
        super(ProjectConfig, self).__init__()
        self['arion'   ] = arion_cfg
        self['election'] = election_cfg
        self['votes'   ] = votes_cfg


### arbitrary config generators ###

@composite
def arionconfig(draw):
    cfg = ArionConfig()
    return cfg

@composite
def voteconfig(draw):
    n_cast  = draw(integers(min_value=0, max_value=10))
    n_spoil = draw(integers(min_value=0, max_value=10))
    return VoteConfig(n_cast, n_spoil)

@composite
def contestconfig(draw):
    # TODO do we need to assume there's at least one vote per contest?
    return ContestConfig(
        question = 'Are pineapples cool?',
        answers = {
            'Yes'    : draw(voteconfig()),
            'No'     : draw(voteconfig()),
            'Unsure' : draw(voteconfig()),
        },
    )

@composite
def contestsconfig(draw):

    contest1 = draw(contestconfig())
    cfg = [contest1]

    # current code will fail if there isn't at least one cast + one spoiled vote
    # TODO would just force creating the record dirs solve that?
    n_cast = sum(
        sum([
            vcfg['cast']
            for vcfg in contest['answers'].values()
        ])
        for contest in cfg
    )
    n_spoil = sum(
        sum([
            vcfg['spoil']
            for vcfg in contest['answers'].values()
        ])
        for contest in cfg
    )
    assume(n_cast  > 0)
    assume(n_spoil > 0)

    return cfg

@composite
def electionconfig(draw):
    kwargs = {}
    kwargs['guardians_count' ] = draw(integers(min_value=2, max_value=3))
    kwargs['guardians_quorum'] = draw(integers(min_value=1, max_value=kwargs['guardians_count'])) # TODO -1?
    kwargs['devices_count'   ] = draw(integers(min_value=1, max_value=3))
    kwargs['verifiers_count' ] = draw(integers(min_value=1, max_value=3))
    cfg = ElectionConfig(**kwargs)
    return cfg

@composite
def projectconfig(draw):
    arion_cfg    = draw(arionconfig())
    election_cfg = draw(electionconfig())
    votes_cfg    = draw(contestsconfig())
    cfg = ProjectConfig(arion_cfg=arion_cfg, election_cfg=election_cfg, votes_cfg=votes_cfg)
    return cfg


### config tests ###

def assert_json_roundtrip(cfg):
    tmp  = json.dumps(cfg)
    cfg2 = json.loads(tmp)
    assert cfg == cfg2

@given(cfg=arionconfig())
@settings(max_examples=1)
def test_roundtrip_arionconfig(cfg: ArionConfig):
    assert_json_roundtrip(cfg)

@given(cfg=voteconfig())
@settings(max_examples=1_000)
def test_roundtrip_voteconfig(cfg: VoteConfig):
    assert_json_roundtrip(cfg)

@given(cfg=contestconfig())
@settings(max_examples=1_000)
def test_roundtrip_contestconfig(cfg: ContestConfig):
    assert_json_roundtrip(cfg)

@given(cfg=electionconfig())
@settings(max_examples=1_000)
def test_roundtrip_electionconfig(cfg: ElectionConfig):
    assert_json_roundtrip(cfg)

@given(cfg=projectconfig())
@settings(max_examples=1_000)
def test_roundtrip_projectconfig(cfg: ProjectConfig):
    assert_json_roundtrip(cfg)
