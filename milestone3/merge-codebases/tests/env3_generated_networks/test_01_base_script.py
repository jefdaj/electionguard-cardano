import pytest
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *


@st.composite
def cfg_base_script(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '01_base_script.sh'),),
        ),
    ])
    return cfg


def assert_base_script(cfg):
    assert_script_logs_match(cfg, '.*', [
        '^cleanup here$',
        '^report here$',
    ])
    assert_node_logs_match(cfg, '.*', ['Stopped.*node.$'])


@given_cached_tests(cfg_base_script(), max_examples=1)
def test_base_script(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_base_script(cfg)
