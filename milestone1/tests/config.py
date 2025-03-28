#!/usr/bin/env python3

import json
import os

from hypothesis import given, settings, assume
from hypothesis.strategies import integers, composite, lists, sampled_from
from hypothesis import note
from typing import Callable, Dict, List


# This has to be defined in a separate file from the actual attack functions
# (they live in scripts/attack.py) because they run in electionguard-python
# containers, whereas this runs on the host system and will not necessarily be
# able to import the electionguard module.
ATTACKS = {

    'admin_withhold_manifest'          : {'who': 'admin' , 'when': ['build_manifest']},
    'device_withhold_submitted_ballot' : {'who': 'device', 'when': ['vote_commit_all']},
    'device_withhold_cast_ballot'      : {'who': 'device', 'when': ['vote_reveal_all']},
    'device_withhold_spoiled_ballot'   : {'who': 'device', 'when': ['vote_reveal_all']},
    'admin_ghost_after_vote'           : {'who': 'admin', 'when': ['tally', 'decrypt_results']},

    # Things not verified in the current implementation:
    # 'admin_break_constants'            : {'who': 'admin' , 'when': ['build_election']},
    # 'device_break_submitted_ballot'    : {'who': 'device', 'when': ['vote_commit_all']},
    # 'device_break_spoiled_ballot'      : {'who': 'device', 'when': ['vote_reveal_all']},

}


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

# name of an attack function
AttackFnName = str

class AttackConfig(list):
    def __init__(self, attacks: List[AttackFnName]):
        super(AttackConfig, self).__init__()
        for fn_name in attacks:
            self.append(fn_name)

class RunConfig(dict):
    def __init__(self, arion_cfg, election_cfg, votes_cfg, attack_cfg):
        super(RunConfig, self).__init__()
        self['arion'   ] = arion_cfg
        self['election'] = election_cfg
        self['votes'   ] = votes_cfg
        self['attacks' ] = attack_cfg


### arbitrary config generators ###

@composite
def arionconfig(draw):
    cfg = ArionConfig()
    return cfg

@composite
def voteconfig(draw):
    n_cast  = draw(integers(min_value=0, max_value=3))
    n_spoil = draw(integers(min_value=0, max_value=3))
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

    # This isn't technically necessary; we handle zero-vote elections properly
    # now. But they tend to waste a lot of test runs, so we keep remove them.
    # It would be fine to comment this out and raise max_examples though.
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
    assume(n_cast + n_spoil > 0)

    return cfg

@composite
def electionconfig(draw):
    kwargs = {}
    kwargs['guardians_count' ] = draw(integers(min_value=2, max_value=3))
    kwargs['guardians_quorum'] = draw(integers(min_value=1, max_value=kwargs['guardians_count'])) # TODO -1?
    kwargs['devices_count'   ] = draw(integers(min_value=1, max_value=3))
    kwargs['verifiers_count' ] = draw(integers(min_value=1, max_value=3)) # TODO allow 0?
    cfg = ElectionConfig(**kwargs)
    return cfg

@composite
def attackconfig(draw, explicit_cfg=None):
    if explicit_cfg is not None:
        return explicit_cfg
    attacks = draw(lists(
        sampled_from(list(ATTACKS.keys())),
        min_size=1,

        # TODO how many would be useful? at least 3-4 right?
        #      but only with enough examples to catch unusual combinations
        max_size=2
    ))
    cfg = AttackConfig(attacks=attacks)
    return cfg

# Messed up election with attacks
@composite
def attackrun(draw, explicit_cfg=None):
    arion_cfg    = draw(arionconfig())
    election_cfg = draw(electionconfig())
    votes_cfg    = draw(contestsconfig())
    attack_cfg   = draw(attackconfig(explicit_cfg=explicit_cfg))
    cfg = RunConfig(
        arion_cfg=arion_cfg,
        election_cfg=election_cfg,
        votes_cfg=votes_cfg,
        attack_cfg=attack_cfg
    )
    return cfg

# Honest/clean election (no attacks)
# TODO dry this out more?
@composite
def honestrun(draw):
    arion_cfg    = draw(arionconfig())
    election_cfg = draw(electionconfig())
    votes_cfg    = draw(contestsconfig())
    attack_cfg  = draw(attackconfig())
    cfg = RunConfig(
        arion_cfg=arion_cfg,
        election_cfg=election_cfg,
        votes_cfg=votes_cfg,
        attack_cfg=[] # only difference
    )
    return cfg


### tests ###

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

@given(cfg=attackconfig())
@settings(max_examples=1_000)
def test_roundtrip_attackcfg(cfg: AttackConfig):
    assert_json_roundtrip(cfg)

@given(cfg=honestrun())
@settings(max_examples=1_000)
def test_roundtrip_honestrun(cfg: RunConfig):
    assert_json_roundtrip(cfg)

@given(cfg=attackrun())
@settings(max_examples=1_000)
def test_roundtrip_attackrun(cfg: RunConfig):
    assert_json_roundtrip(cfg)
