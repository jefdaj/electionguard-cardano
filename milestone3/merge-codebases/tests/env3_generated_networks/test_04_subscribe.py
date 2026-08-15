import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import assert_wallet_created
from .test_03_node_ready    import assert_node_ready


@st.composite
def cfg_subscribe_txt(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = f'install_qr_txt',
            args = (('drawn', draw(st.integers(0, 1000))),)
        ),
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '04_subscribe_txt.sh'),),
        ),
    ])
    return cfg


def assert_endelection_event(cfg):
    assert_script_logs_match(cfg, '(?!admin)', [
        # some of the test qr_strs point to elections that never finished,
        # so timing out is the expected/correct behavior
        '^[0-9]{9,}\\s.*(ended election|subscriber timed out)'
   ])


@given_cached_tests(
    cfg_strategy = cfg_subscribe_txt(),
    max_examples = 1,
)
def test_subscribe_txt(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)


@st.composite
def cfg_subscribe_png(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = f'install_qr_png',
            args = (('drawn', draw(st.integers(0, 1000))),)
        ),
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', '04_subscribe_png.sh'),),
        ),
    ])
    return cfg


@given_cached_tests(
    cfg_strategy = cfg_subscribe_png(),
    max_examples = 1,
)
def test_subscribe_png(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
