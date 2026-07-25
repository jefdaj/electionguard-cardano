import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def wallet_config(draw):
    fn_name  = sys._getframe().f_code.co_name
    cfg = draw( hashed_test_config() )
    cfg = deep_replace(
        cfg,
        'pytest.config_fns.names',
        tuple(list(cfg.pytest.config_fns.names) + [fn_name])
    )
    cfg = deep_replace(
        cfg,
        'pytest.setup_fns',
        SetupFnsConfig(fns=(
            FnCallConfig(
                name = 'render_egc_scripts',
                args = (('default', 'wallet.sh'),),
            ),
        )),
    )
    return cfg

@given_cached_tests(wallet_config, max_examples=1)
def test_create_wallet(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^\\s*"addr": "addr_test1')
