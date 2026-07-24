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
def node_ready_config(draw):
    cfg = draw( hashed_test_config() )
    attr_paths = [
        'nodes.admin.script',
        'nodes.guardians.script',
        'nodes.devices.script',
        'nodes.verifiers.script',
    ]
    for attr_path in attr_paths:
        cfg = deep_replace(cfg, attr_path, 'node-ready.sh')
    return cfg


@seed(get_random_seed())
@settings(
    max_examples=5,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=node_ready_config())
def test_node_ready(cfg: HashedTestConfig, tmp_root: Path, env3_arion_dir: Path):
    resolved_cfg = resolve_test_config(cfg=cfg, tmp_root=tmp_root)
    init_test_tmpdir(cfg=resolved_cfg)
    # TODO avoid clobbering previous file here!
    # TODO and add a log assertion about node being ready
    with lock_test_tmpdir(cfg=resolved_cfg): # as test_tmpdir:
        with arion_network_up(test_cfg=resolved_cfg, arion_dir=env3_arion_dir): #  as network_name:
            run_egc_scripts(test_cfg=resolved_cfg, arion_dir=env3_arion_dir)
