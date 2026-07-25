import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def config_subscribe_str(draw):
    cfg      = draw( hashed_test_config() )
    fn_name  = sys._getframe().f_code.co_name
    cfg      = deep_replace(cfg, 'pytest.config_fns', cfg.pytest.config_fns + [fn_name])
    n        = draw(integers(0, 1000)) # mod will be used to pick qr_str index
    sub_call = FnCallConfig(name='write_qr_str', args=(('drawn', n),))
    cfg      = deep_replace(cfg, 'pytest.setup_fns', cfg.pytest.config_fns + [sub_call])
    # TODO also need to set the default template -> subscribe.sh
    return cfg

@given_cached_tests(
    cfg_strategy = config_subscribe_str,
    max_examples = 3,
)
def test_subscribe_old_qr_str(cfg: ResolvedTestConfig):
    # TODO catch elections that stalled or burned test tokens too
    assert_node_logs_match(cfg=cfg, pattern='^ElectionEvent.*ended election')
