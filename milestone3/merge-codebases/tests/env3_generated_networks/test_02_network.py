import pytest
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace


# These only test Cardano/Ogmios. Since there's an IPFS container per pair in
# this env, it'll need to be tested separately. 

@st.composite
def await_node_ready_config(draw):
    cfg = draw( hashed_test_config() )
    attr_paths = [
        'nodes.admin.script',
        'nodes.guardians.script',
        'nodes.devices.script',
        'nodes.verifiers.script',
    ]
    for attr_path in attr_paths:
        cfg = deep_replace(cfg, attr_path, 'await-node-ready.sh')
    print(f'cfg: {cfg}')
    return cfg


@seed(get_random_seed())
@settings(
    max_examples=3,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=await_node_ready_config())
def test_node_await(cfg: HashedTestConfig, tmp_root: Path, env3_arion_dir: Path):

    resolved_cfg = resolve_test_config(cfg=cfg, tmp_root=tmp_root)
    init_test_tmpdir(cfg=resolved_cfg)

    with lock_test_tmpdir(cfg=resolved_cfg) as test_tmpdir:
        with arion_network_up(test_cfg=resolved_cfg, arion_dir=env3_arion_dir) as network_name:

            health = ogmios_health_sync()
            status = health["connectionStatus"]
            sync   = health["networkSynchronization"]
            if status != "connected":
                raise RuntimeError(f"Ogmios not connected to node: {health}")
            if not isinstance(sync, (int, float)) or sync < 0.999:
                raise RuntimeError(f"Ogmios not synced (networkSynchronization={sync}): {health}")
            assert health["network"] == "preview"


# @seed(get_random_seed())
# @settings(
#     max_examples=3,
#     deadline=None,
#     phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
#     # database defaults on -> failing configs replay next run
# )
# @given(cfg=hashed_test_config())
# def test_ogmios_query(cfg: HashedTestConfig, tmp_root: Path, env3_arion_dir: Path):
# 
#     resolved_cfg = resolve_test_config(cfg=cfg, tmp_root=tmp_root)
#     init_test_tmpdir(cfg=resolved_cfg)
# 
#     with lock_test_tmpdir(cfg=resolved_cfg) as test_tmpdir:
#         with arion_network_up(test_cfg=resolved_cfg, arion_dir=env3_arion_dir) as network_name:
# 
#             tip = query_network_tip_sync()
#             assert isinstance(tip, dict)
#             assert isinstance(tip['slot'], int)
#             assert isinstance(tip['block_hash'], str)
