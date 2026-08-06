import pytest
import sys
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from dataclasses import replace
from egc import *
from ..lib import *
from .lib  import *


@st.composite
def config_subscribe_qr_txt(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', f'subscribe-qr-txt.sh'),),
        ),
        FnCallConfig(
            name = f'install_qr_txt',
            args = (('drawn', draw(st.integers(0, 1000))),)
        )
    ])
    return cfg

@given_cached_tests(
    cfg_strategy = config_subscribe_qr_txt(),
    max_examples = 3,
)
def test_subscribe_qr_txt(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, '.*', ['^[0-9]{9,}\\s.*ended election'])
    assert_script_logs_do_not_match(cfg, '.*', ['^Traceback', '^arion: FatalError'])


@st.composite
def config_subscribe_qr_png(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (('default', f'subscribe-qr-png.sh'),),
        ),
        FnCallConfig(
            name = f'install_qr_png',
            args = (('drawn', draw(st.integers(0, 1000))),)
        )
    ])
    return cfg

@given_cached_tests(
    cfg_strategy = config_subscribe_qr_png(),
    max_examples = 10,
)
def test_subscribe_qr_png(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, '.*', [

        # some of the test qr_strs point to elections that never finished
        # TODO separate timeout test
        '^[0-9]{9,}\\s.*(ended election|subscriber timed out)'

    ])
    assert_script_logs_do_not_match(cfg, '.*', ['^Traceback', '^arion: FatalError'])
