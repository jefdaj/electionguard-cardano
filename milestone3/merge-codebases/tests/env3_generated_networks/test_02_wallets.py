import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def wallet_config(draw):
    cfg = draw( test_config() )
    cfg = replace(cfg, cfg_type = sys._getframe().f_code.co_name)
    for nodes in ['admin', 'guardians', 'devices', 'verifiers']:
        attr_path = f'nodes.{nodes}.template'
        cfg = deep_replace(cfg, attr_path, 'wallet.sh')
    return cfg

@given_cached_tests(wallet_config, max_examples=1)
def test_create_wallet(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^\\s*"addr": "addr_test1')
