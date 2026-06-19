import pytest
from egc import *

@pytest.mark.testnet
def test_ogmios_ready(ogmios: OgmiosV6ChainContext):
    health = ogmios_health_sync()
    status = health.get("connectionStatus")
    sync   = health.get("networkSynchronization")
    if status != "connected":
        raise RuntimeError(f"Ogmios not connected to node: {health}")
    if not isinstance(sync, (int, float)) or sync < 0.999:
        raise RuntimeError(f"Ogmios not synced (networkSynchronization={sync}): {health}")
    assert health["network"] == "preview"

@pytest.mark.testnet
def test_query_network_tip(ogmios: OgmiosV6ChainContext):
    tip = query_network_tip_sync()
    assert isinstance(tip, dict)
    assert isinstance(tip['slot'], int)
    assert isinstance(tip['block_hash'], str)
