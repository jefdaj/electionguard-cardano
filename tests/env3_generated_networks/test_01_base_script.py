import pytest
from hypothesis import strategies as st
from .lib import (FnCallConfig, ResolvedTestConfig, append_config_fn_name, append_setup_fns,
                  assert_node_logs_match, assert_script_logs_match, assert_test_completed,
                  cfg_test_base, given_cached_tests)


@st.composite
def cfg_base_script(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '01_base_script.sh'),
            ),
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
