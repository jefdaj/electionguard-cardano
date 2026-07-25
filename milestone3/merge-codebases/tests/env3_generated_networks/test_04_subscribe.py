import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def subscribe_config(draw):
    cfg = draw( hashed_test_config() )
    cfg = replace(cfg, cfg_type = sys._getframe().f_code.co_name)
    for nodes in ['admin', 'guardians', 'devices', 'verifiers']:
        attr_path = f'nodes.{nodes}.template'
        cfg = deep_replace(cfg, attr_path, 'subscribe.sh')
    return cfg

@given_cached_tests(subscribe_config, max_examples=1)
def test_subscribe_to_old_election(cfg: ResolvedTestConfig):
    # assert_node_logs_match(cfg=cfg, pattern='^\\s*"addr": "addr_test1')
    pass
