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
        'nodes.admin.template',
        'nodes.guardians.template',
        'nodes.devices.template',
        'nodes.verifiers.template',
    ]
    for attr_path in attr_paths:
        cfg = deep_replace(cfg, attr_path, 'node-ready.sh')
    return cfg

# TODO remove tmp_root, arion_dir?
@given_cached_tests(hashed_test_config, max_examples=1)
# def test_node_ready(cfg: ResolvedTestConfig, tmp_root: Path, env3_arion_dir: Path):
def test_node_ready(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^node is ready')
