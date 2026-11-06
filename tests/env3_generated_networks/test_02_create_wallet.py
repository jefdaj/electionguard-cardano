import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from .lib import (FnCallConfig, ResolvedTestConfig, append_config_fn_name, append_setup_fns,
                  assert_node_logs_match, assert_script_logs_match, assert_test_completed,
                  cfg_test_base, given_cached_tests, st)


@st.composite
def cfg_create_wallet(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '02_create_wallet.sh'),),
        ),
    ])
    return cfg


def assert_wallet_created(cfg):
    assert_script_logs_match(cfg, '.*', [
        '^{.*"addr": "addr_test1'
    ])
    assert_node_logs_match(cfg, '.*', [
        'PUT /api/wallet',
        'Generated /data/private/wallet.sk$',
    ])


@given_cached_tests(cfg_create_wallet(), max_examples=1)
def test_create_wallet(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
