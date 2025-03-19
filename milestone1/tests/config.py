#!/usr/bin/env python3

import os
import json

from hypothesis import given, settings
from hypothesis.strategies import integers, composite, SearchStrategy
from typing import Callable


### verbose but simple config definition ###

# TODO move to /tmp?
# TMPDIR_PREFIX = './tests'

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
        # self['data_dir'] = os.path.join(TMPDIR_PREFIX, test_name)
        self['data_dir'] = 'data'
        self['bind_mounts'] = BindMountsConfig()

class VoteConfig(dict):
    def __init__(self, n_cast: int, n_spoil: int):
        assert n_cast  >= 0
        assert n_spoil >= 0
        self['cast' ] = n_cast
        self['spoil'] = n_spoil

class VotesConfig(dict):
    def __init__(self):
        super(VotesConfig, self).__init__()
        self["Yes"   ] = VoteConfig(3, 1)
        self["No"    ] = VoteConfig(2, 2)
        self["Unsure"] = VoteConfig(1, 3)

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
        self['question' ] = 'Are pineapples cool?'

class ProjectConfig(dict):
    def __init__(self, *args, **kwargs):
        super(ProjectConfig, self).__init__()
        self['arion'   ] = ArionConfig()
        self['election'] = ElectionConfig(*args, **kwargs)
        self['votes'   ] = VotesConfig()


### config tests ###

# TODO why doesn't this quite work when round-tripped to JSON as part of projectconfig below?
# @composite
# def arionconfig(draw):
#     n: int = draw(integers(min_value=1000, max_value=9999))
#     test_name = f'test{n}'
#     cfg = ArionConfig(test_name)
#     return cfg

@composite
def projectconfig(draw):

    kwargs = {}
    kwargs['guardians_count' ] = draw(integers(min_value=2, max_value=10))
    kwargs['guardians_quorum'] = draw(integers(min_value=1, max_value=kwargs['guardians_count'])) # TODO -1?
    kwargs['devices_count'   ] = draw(integers(min_value=1, max_value=10))
    kwargs['verifiers_count' ] = draw(integers(min_value=1, max_value=10))
    cfg = ProjectConfig(**kwargs)
    return cfg

@given(cfg=projectconfig())
@settings(max_examples=1_000)
def test_projectconfig_json_roundtrip(cfg: ProjectConfig):
    tmp  = json.dumps(cfg)
    cfg2 = json.loads(tmp)
    assert cfg == cfg2
