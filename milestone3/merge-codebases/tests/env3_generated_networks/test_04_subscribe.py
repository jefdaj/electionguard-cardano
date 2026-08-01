import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *

def config_subscribe_qr(fmt='txt'):
    @st.composite
    def draw_fn(draw):
        cfg = draw( config_test_base() )
        cfg = append_config_fn_name(cfg)
        cfg = replace_setup_fns(cfg, [
            FnCallConfig(
                name = 'render_egc_scripts',
                args = (('default', f'subscribe-qr-{fmt}.sh'),),
            ),
            FnCallConfig(
                name = f'write_qr_{fmt}',
                args = (('drawn', draw(st.integers(0, 1000))),)
            )
        ])
        return cfg
    fn_name = sys._getframe().f_code.co_name
    draw_fn.__name__ = fn_name
    return draw_fn

@given_cached_tests(
    cfg_strategy = config_subscribe_qr('txt'),
    max_examples = 3,
)
def test_subscribe_qr_str(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^[0-9]{9,}\\s.*ended election')
    assert_node_logs_do_not_match(cfg=cfg, pattern='^arion: FatalError')

@given_cached_tests(
    cfg_strategy = config_subscribe_qr('png'),
    max_examples = 3,
)
def test_subscribe_qr_png(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^[0-9]{9,}\\s.*ended election')
    assert_node_logs_do_not_match(cfg=cfg, pattern='^arion: FatalError')
