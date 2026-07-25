import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

# TODO wait, does this also need to be hashed??
# TODO how to make these easier to debug?
@st.composite
def setup_old_qr_str(draw):
    print('running setup_old_qr_str')
    i = draw(st.integers(0, len(OLD_QR_STRS)))
    return write_qr_str

@st.composite
def subscribe_old_qr_str_config(draw):
    cfg = draw( hashed_test_config() )
    cfg = replace(cfg, cfg_type = sys._getframe().f_code.co_name)
    for nodes in ['admin', 'guardians', 'devices', 'verifiers']:
        attr_path = f'nodes.{nodes}.template'
        cfg = deep_replace(cfg, attr_path, 'subscribe.sh')
    return cfg

@given_cached_tests(
    cfg_strategy   = subscribe_old_qr_str_config,
    setup_strategy = setup_old_qr_str,
    max_examples   = 3,
)
def test_subscribe_old_qr_str(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^ElectionEvent.*ended election')
