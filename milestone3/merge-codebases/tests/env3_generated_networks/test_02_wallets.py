import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *

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

@given_cached_tests(config_wallet, max_examples=1)
def test_create_wallet(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^\\s*"addr": "addr_test1')
    assert_node_logs_do_not_match(cfg=cfg, pattern='^arion: FatalError')
