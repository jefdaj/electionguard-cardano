import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *


@st.composite
def cfg_node_ready(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '03_node_ready.sh'),),
        ),
    ])
    return cfg


def assert_node_ready(cfg):
    assert_script_logs_match(cfg, '.*', [
        '"cardano": {"connected": true, "sync_percent": 100',
        '"ipfs": {"connected": true',
    ])


@given_cached_tests(cfg_node_ready(), max_examples=1)
def test_node_ready(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_node_ready(cfg)
