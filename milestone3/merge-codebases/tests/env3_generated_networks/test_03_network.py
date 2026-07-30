import pytest
import sys
from hypothesis import given, settings, seed, Phase
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def node_ready_config(draw):
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
                args = (('default', 'node-ready.sh'),),
            ),
        )),
    )
    return cfg

@given_cached_tests(node_ready_config, max_examples=3)
def test_node_ready(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^node is ready$')
    assert_node_logs_do_not_match(cfg=cfg, pattern='^arion: FatalError')
