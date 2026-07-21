import pytest
from egc import *
from helpers_env3 import assert_json_roundtrip


### round-trip configs to json ###

@given(cfg=voteconfig())
@settings(max_examples=1_000)
def test_json_voteconfig(cfg: VoteConfig):
    assert_json_roundtrip(cfg)

@given(cfg=contestconfig())
@settings(max_examples=1_000)
def test_json_contestconfig(cfg: ContestConfig):
    assert_json_roundtrip(cfg)

@given(cfg=electionconfig())
@settings(max_examples=1_000)
def test_json_electionconfig(cfg: ElectionConfig): # TODO have to rename this?
    assert_json_roundtrip(cfg)


### test tmpdir setup ###

def test_env3_tmpdir(env3_tmpdir: Path):
    assert env3_tmpdir.exists()
    # TODO finish

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
