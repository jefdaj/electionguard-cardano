import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

def config_subscribe_qr(variant='txt'):
    # TODO is this overcomplicating how to call it?
    fn_name = f'config_subscribe_qr_{variant}'
    @st.composite
    def draw_fn(draw):
        cfg = draw( hashed_test_config() )

        # TODO util fn:
        cfg = deep_replace(
            cfg,
            'pytest.config_fns.names',
            tuple(list(cfg.pytest.config_fns.names) + [fn_name])
        )

        n = draw(st.integers(0, 1000)) # mod will be used to pick qr_str index
        sub_call = FnCallConfig(name=f'write_qr_{variant}', args=(('drawn', n),))
        cfg = deep_replace(
            cfg,
            'pytest.setup_fns',
            SetupFnsConfig(fns=(
                FnCallConfig(
                    name = 'render_egc_scripts',
                    args = (('default', f'subscribe-qr-{variant}.sh'),),
                ),
                sub_call,
            )),
        )
        return cfg
    draw_fn.__name__ = fn_name
    return draw_fn

@given_cached_tests(
    cfg_strategy = config_subscribe_qr('txt'),
    max_examples = 3,
)
def test_subscribe_old_qr_str(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^[0-9]{9,}\\s.*ended election')

@given_cached_tests(
    cfg_strategy = config_subscribe_qr('png'),
    max_examples = 3,
)
def test_subscribe_old_qr_png(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^[0-9]{9,}\\s.*ended election')
