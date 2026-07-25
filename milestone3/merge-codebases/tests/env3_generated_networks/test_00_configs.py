import pytest
from hypothesis import given, settings
from pathlib import Path

from egc import *
# from ..lib import *
from ..lib.json_utils import assert_json_roundtrip
from .lib.test_config import *


### round-trip configs to json ###

@given(cfg=votes_config())
@settings(max_examples=1_000)
def test_roundtrip_vote_config(cfg: VotesConfig):
    assert_json_roundtrip(cfg)

@given(cfg=contests_config())
@settings(max_examples=1_000)
def test_roundtrip_contests_config(cfg: ContestsConfig):
    assert_json_roundtrip(cfg)

@given(cfg=guardians_config())
@settings(max_examples=1_000)
def test_roundtrip_guardians_config(cfg: GuardiansConfig):
    assert_json_roundtrip(cfg)

# TODO @example instead
@given(cfg=arion_config())
@settings(max_examples=1)
def test_roundtrip_arion_config(cfg: ArionConfig):
    assert_json_roundtrip(cfg)

@given(cfg=devices_config())
@settings(max_examples=1_000)
def test_roundtrip_devices_config(cfg: DevicesConfig):
    assert_json_roundtrip(cfg)

@given(cfg=verifiers_config())
@settings(max_examples=1_000)
def test_roundtrip_verifiers_config(cfg: VerifiersConfig):
    assert_json_roundtrip(cfg)

@given(cfg=nodes_config())
@settings(max_examples=1_000)
def test_roundtrip_nodes_config(cfg: NodesConfig):
    assert_json_roundtrip(cfg)

@given(cfg=setup_fns_config())
@settings(max_examples=1)
def test_roundtrip_setup_fns_config(cfg: SetupFnsConfig):
    assert_json_roundtrip(cfg)

# TODO @example instead
@given(cfg=attack_fns_config())
@settings(max_examples=1)
def test_roundtrip_attack_fns_config(cfg: AttackFnsConfig):
    assert_json_roundtrip(cfg)

# @example(cfg=example_test_config())
@given(cfg=hashed_test_config())
@settings(max_examples=1_000)
def test_roundtrip_hashed_test_config(cfg: HashedTestConfig):
    assert_json_roundtrip(cfg)
