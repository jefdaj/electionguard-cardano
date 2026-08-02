import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *

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

@given_cached_tests(config_node_ready, max_examples=3)
def test_node_ready(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg, '.*', '^node is ready$')
    assert_node_logs_do_not_match(cfg, '.*', '^arion: FatalError')
