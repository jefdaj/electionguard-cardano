import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *

from .test_03_network import NODE_READY_CONFIGS

@st.composite
def config_wallet(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', 'wallet.sh'),),
        ),
    ])
    return cfg

WALLET_CONFIGS = [f() for f in [
    config_wallet,
]] + NODE_READY_CONFIGS

@given_cached_tests(st.one_of(WALLET_CONFIGS), max_examples=3)
def test_create_wallet(cfg: ResolvedTestConfig):
    assert_script_logs_do_not_match(cfg, '.*', ['^Traceback', '^arion: FatalError', '^cleanup failed$'])
    assert_script_logs_match(cfg, '.*', [
        '^\\s*"addr": "addr_test1'
    ])
    assert_node_logs_match(cfg, '.*', [
        'PUT /api/wallet',
        'Generated /data/private/wallet.sk$',
    ])
