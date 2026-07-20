import pytest
from egc import *

def test_ipfs_stable(ipfs):
    status = ipfs_status_sync()
    assert status['n_peers'] >= 3

def test_ogmios_synced(ogmios: OgmiosV6ChainContext):
    health = ogmios_health_sync()
    status = health["connectionStatus"]
    sync   = health["networkSynchronization"]
    if status != "connected":
        raise RuntimeError(f"Ogmios not connected to node: {health}")
    if not isinstance(sync, (int, float)) or sync < 0.999:
        raise RuntimeError(f"Ogmios not synced (networkSynchronization={sync}): {health}")
    assert health["network"] == "preview"

def test_ogmios_query(ogmios: OgmiosV6ChainContext):
    tip = query_network_tip_sync()
    assert isinstance(tip, dict)
    assert isinstance(tip['slot'], int)
    assert isinstance(tip['block_hash'], str)
