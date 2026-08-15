from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import assert_wallet_created
from .test_03_node_ready    import assert_node_ready
from .test_04_subscribe     import assert_endelection_event
from .test_06_admin_post_ipfs import assert_admin_post_ipfs
from .test_07_post_manifest import cfg_post_manifest_base, assert_post_manifest
from .test_08_post_batch    import assert_advance_phase, assert_post_ceremony


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


@given_cached_tests(
    cfg_strategy = cfg_advance_phase(),
    max_examples = 1,
)
def test_advance_phase(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
    assert_admin_post_ipfs(cfg)
    assert_post_manifest(cfg)
    assert_post_ceremony(cfg)
    assert_advance_phase(cfg, ElectionConfigPhase(ConfigCeremonyPhase()))
    assert_advance_phase_standalone(cfg)
