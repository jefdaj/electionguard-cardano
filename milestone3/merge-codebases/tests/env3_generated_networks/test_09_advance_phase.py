from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_04_subscribe     import assert_election_events
from .test_07_post_manifest import cfg_post_manifest_base


@st.composite
def cfg_advance_phase(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '09_await_phase.sh'),
                ('admin', '09_advance_phase.sh'),
            ),
        ),
    ])
    return cfg


def assert_advance_phase_standalone(cfg):
    assert_script_logs_match(cfg, 'admin', [
        '^config_ceremony_round1$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'PUT /api/phase.*201$',
    ])
    assert_node_logs_match(cfg, '.*', [
        'GET /api/phase/await.*201$',
    ])


@given_cached_tests(cfg_strategy=cfg_advance_phase(), max_examples=1)
def test_advance_phase(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_election_events(cfg)
    assert_advance_phase_standalone(cfg)
