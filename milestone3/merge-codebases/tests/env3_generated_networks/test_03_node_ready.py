import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import *


@st.composite
def cfg_node_ready(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '03_node_ready.sh'),),
        ),
    ])
    return cfg


def assert_node_ready(cfg):
    assert_script_logs_match(cfg, '.*', ['^node is ready$'])


@given_cached_tests(cfg_node_ready(), max_examples=1)
def test_node_ready(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
