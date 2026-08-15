from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

# from .test_07_post_manifest import *


@st.composite
def cfg_advance_phase(draw):
    cfg = draw( cfg_post_ceremony_base() ) # TODO would cfg_init_election work here?
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '09_await_phase.sh'),
                ('admin', '09_advance_phase.sh'),
            ),
        ),
    ])
    return cfg


@given_cached_tests(
    cfg_strategy = cfg_advance_phase(),
    max_examples = 1,
)
def test_advance_phase(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_script_logs_match(cfg, '.*', [
        '^CONFIG_CEREMONY_ROUND1$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'PUT /api/phase.*201$',
    ])
    assert_node_logs_match(cfg, '.*', [
        'GET /api/phase/await.*201$',
    ])
