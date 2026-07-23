import pytest
from hypothesis import given, settings, seed, Phase
from egc import *
from ..lib import *
from .lib  import *


# These only test Cardano/Ogmios. Since there's an IPFS container per pair in
# this env, it'll need to be tested separately. 


@seed(get_random_seed())
@settings(
    max_examples=25,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=hashed_test_config())
def test_ogmios_synced(cfg: HashedTestConfig, tmp_root: Path, env3_arion_dir: Path):

    with resolve_test_config(cfg=cfg, tmp_root=tmp_root) as resolved_cfg:
        with init_test_tmpdir(cfg=resolved_cfg) as test_tmpdir:
            with arion_network_up(cfg=resolved_cfg, arion_dir=env3_arion_dir) as arion_network:

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
def test_ogmios_query(cfg: HashedTestConfig, tmp_root: Path, env3_arion_dir: Path):

    with resolve_test_config(cfg=cfg, tmp_root=tmp_root) as resolved_cfg:
        with init_test_tmpdir(cfg=resolved_cfg) as test_tmpdir:
            with arion_network_up(cfg=resolved_cfg, arion_dir=env3_arion_dir) as arion_network:

                tip = query_network_tip_sync()
                assert isinstance(tip, dict)
                assert isinstance(tip['slot'], int)
                assert isinstance(tip['block_hash'], str)
