import pytest
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *


@st.composite
def cfg_cleanup_called(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '01_cleanup.sh'),),
        ),
    ])
    return cfg


def assert_cleanup_called(cfg):
    assert_script_logs_match(cfg, '.*', ['^cleaning up$'])


@given_cached_tests(cfg_cleanup_called(), max_examples=1)
def test_cleanup_called(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_cleanup_called(cfg)
