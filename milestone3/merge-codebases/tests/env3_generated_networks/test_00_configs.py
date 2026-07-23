import pytest
from hypothesis import given, settings
from pathlib import Path

from egc import *
from ..lib import *
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

@given(cfg=hashed_attacks_config())
@settings(max_examples=1)
def test_roundtrip_attacks_config(cfg: HashedAttacksConfig):
    assert_json_roundtrip(cfg)

# @example(cfg=example_test_config())
@given(cfg=hashed_test_config())
@settings(max_examples=1_000)
def test_roundtrip_hashed_test_config(cfg: HashedTestConfig):
    assert_json_roundtrip(cfg)

@given(cfg=hashed_test_config())
@settings(max_examples=1_000)
def test_roundtrip_resolved_test_config(cfg: HashedTestConfig):
    resolved = ResolvedTestConfig.from_hashed_config(
        cfg = cfg,
        tmp_root = Path('/tmp'), # TODO actual tmp_root?
        )
    assert_json_roundtrip(resolved)



### test tmpdir setup ###

# @given_runconfig()
# def test_env3_tmpdir(env3_tmpdir: Path):
#     assert env3_tmpdir.exists()
#     # TODO finish

### test containers up ###

# def test_ipfs_stable(ipfs):
#     status = ipfs_status_sync()
#     assert status['n_peers'] >= 3
# 
# def test_ogmios_synced(ogmios: OgmiosV6ChainContext):
#     health = ogmios_health_sync()
#     status = health["connectionStatus"]
#     sync   = health["networkSynchronization"]
#     if status != "connected":
#         raise RuntimeError(f"Ogmios not connected to node: {health}")
#     if not isinstance(sync, (int, float)) or sync < 0.999:
#         raise RuntimeError(f"Ogmios not synced (networkSynchronization={sync}): {health}")
#     assert health["network"] == "preview"
# 
# def test_ogmios_query(ogmios: OgmiosV6ChainContext):
#     tip = query_network_tip_sync()
#     assert isinstance(tip, dict)
#     assert isinstance(tip['slot'], int)
#     assert isinstance(tip['block_hash'], str)

# TODO test egc node status
