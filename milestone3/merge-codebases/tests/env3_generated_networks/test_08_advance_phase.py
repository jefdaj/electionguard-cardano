from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

# TODO derive this from config_announce_ceremony instead (need a replace egc script fn)
@st.composite
def config_advance_phase(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', 'await-phase.sh'),
                ('admin', 'advance-phase.sh'),
            ),
        ),
        FnCallConfig(name='install_funder_sk' , args=()),
        FnCallConfig(name='install_node_cfgs' , args=()),
    ])
    return cfg

ADVANCE_PHASE_CONFIGS = [f() for f in [
    config_advance_phase,
]] # TODO more here


@given_cached_tests(
    cfg_strategy = st.one_of(ADVANCE_PHASE_CONFIGS),
    max_examples = 1,
)
def test_advance_phase(cfg: ResolvedTestConfig):
    assert_script_logs_do_not_match(cfg, '.*', [
        'Traceback',
        'arion: FatalError',
        'Command not available from current role',
        '^cleanup failed$',
    ])
    assert_script_logs_match(cfg, '.*', [
        '^CONFIG_CEREMONY_ROUND1$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'PUT /api/phase.*201$',
    ])
    assert_node_logs_match(cfg, '.*', [
        'GET /api/phase/await.*201$',
    ])
