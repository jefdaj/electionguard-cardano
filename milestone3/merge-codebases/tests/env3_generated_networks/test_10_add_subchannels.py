from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import assert_wallet_created
from .test_03_node_ready    import assert_node_ready
from .test_04_subscribe     import assert_election_events
from .test_06_admin_post_ipfs import assert_admin_post_ipfs
from .test_07_post_manifest import cfg_post_manifest_base, assert_post_manifest
from .test_08_post_batch    import assert_advance_phase, assert_post_manifest, assert_post_ceremony


@st.composite
def cfg_add_subchannels(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '10_request_subchannel.sh'),
                ('admin', '10_add_subchannels.sh'),
            ),
        ),
    ])
    return cfg


def assert_add_subchannels(cfg):
    assert_script_logs_match(cfg, 'admin', [
        'egc channel create'
    ])
    assert_node_logs_match(cfg, 'admin', [
        'POST /api/channel/create.*201$',
        'admin sent 5 ADA from admin channel fee pool',
    ])


@given_cached_tests(
    cfg_strategy = cfg_add_subchannels(),
    max_examples = 1,
)
def test_add_subchannels(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    # TODO put back assert_election_events(cfg)
    assert_admin_post_ipfs(cfg)
    # TODO put back assert_post_manifest(cfg)
    # TODO put backassert_post_ceremony(cfg)
    # assert_advance_phase(cfg, ElectionConfigPhase(ConfigCeremonyPhase()))
    assert_add_subchannels(cfg)
