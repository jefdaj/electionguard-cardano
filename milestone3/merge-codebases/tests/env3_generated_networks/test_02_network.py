import pytest
from hypothesis import given, settings, seed, Phase
from egc import *
from ..lib import *
from .lib  import *

# Since there's an IPFS container per pair in this env,
# it'll need to be tested separately.

@seed(get_random_seed())
@settings(
    max_examples=25,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=hashed_test_config())
def test_ogmios_synced(env3_ogmios: OgmiosV6ChainContext, cfg: HashedTestConfig):
    health = ogmios_health_sync()
    status = health["connectionStatus"]
    sync   = health["networkSynchronization"]
    if status != "connected":
        raise RuntimeError(f"Ogmios not connected to node: {health}")
    if not isinstance(sync, (int, float)) or sync < 0.999:
        raise RuntimeError(f"Ogmios not synced (networkSynchronization={sync}): {health}")
    assert health["network"] == "preview"

@seed(get_random_seed())
@settings(
    max_examples=25,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=hashed_test_config())
def test_ogmios_query(env3_ogmios: OgmiosV6ChainContext, cfg: HashedTestConfig):
    tip = query_network_tip_sync()
    assert isinstance(tip, dict)
    assert isinstance(tip['slot'], int)
    assert isinstance(tip['block_hash'], str)
