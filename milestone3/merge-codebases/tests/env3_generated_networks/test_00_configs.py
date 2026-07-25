import pytest
from hypothesis import given, settings
from pathlib import Path

from egc import *
# from ..lib import *
from ..lib.json_utils import assert_json_roundtrip
from .lib.test_config import *


### round-trip configs to json ###

@given(cfg=hashed_votes_config())
@settings(max_examples=1_000)
def test_roundtrip_vote_config(cfg: HashedVotesConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_contests_config())
@settings(max_examples=1_000)
def test_roundtrip_contests_config(cfg: HashedContestsConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_guardians_config())
@settings(max_examples=1_000)
def test_roundtrip_guardians_config(cfg: HashedGuardiansConfig):
    assert_json_roundtrip(cfg)

# TODO @example instead
@given(cfg=hashed_arion_config())
@settings(max_examples=1)
def test_roundtrip_arion_config(cfg: HashedArionConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_devices_config())
@settings(max_examples=1_000)
def test_roundtrip_devices_config(cfg: HashedDevicesConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_verifiers_config())
@settings(max_examples=1_000)
def test_roundtrip_verifiers_config(cfg: HashedVerifiersConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_nodes_config())
@settings(max_examples=1_000)
def test_roundtrip_nodes_config(cfg: HashedNodesConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_setup_fns_config())
@settings(max_examples=1)
def test_roundtrip_setup_fns_config(cfg: HashedSetupFnsConfig):
    assert_json_roundtrip(cfg)

# TODO @example instead
@given(cfg=hashed_attack_fns_config())
@settings(max_examples=1)
def test_roundtrip_attack_fns_config(cfg: HashedAttackFnsConfig):
    assert_json_roundtrip(cfg)

# @example(cfg=example_test_config())
@given(cfg=hashed_test_config())
@settings(max_examples=1_000)
def test_roundtrip_hashed_test_config(cfg: HashedTestConfig):
    assert_json_roundtrip(cfg)
