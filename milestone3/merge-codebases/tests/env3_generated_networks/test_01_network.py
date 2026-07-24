import pytest
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def node_ready_config(draw):
    cfg = draw( hashed_test_config() )
    for nodes in ['admin', 'guardians', 'devices', 'verifiers']:
        attr_path = f'nodes.{nodes}.template'
        cfg = deep_replace(cfg, attr_path, 'node-ready.sh')
    return cfg

@given_cached_tests(hashed_test_config, max_examples=3)
def test_node_ready(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^node is ready$')

@given_cached_tests(hashed_test_config, max_examples=3)
def test_cleanup_called(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^cleaning up$')
