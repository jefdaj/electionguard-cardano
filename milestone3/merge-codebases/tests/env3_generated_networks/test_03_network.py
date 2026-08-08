import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *

from .test_04_subscribe import config_subscribe_qr_txt, config_subscribe_qr_png
from .test_05_init_election import INIT_ELECTION_CONFIGS

@st.composite
def config_node_ready(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', 'node-ready.sh'),),
        ),
    ])
    return cfg

# These all include making sure the node is ready
# TODO when should the composite functions be called?
NODE_READY_CONFIGS = [f() for f in [
    config_node_ready,
    config_subscribe_qr_txt,
    config_subscribe_qr_png,
]] + INIT_ELECTION_CONFIGS

@given_cached_tests(st.one_of(NODE_READY_CONFIGS), max_examples=10)
def test_node_ready(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, '.*', ['^node is ready$'])
    assert_script_logs_do_not_match(cfg, '.*', [
        '^Traceback',
        '^arion: FatalError',
        '"connected": false',
    ])
