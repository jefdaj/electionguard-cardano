from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import assert_wallet_created
from .test_03_node_ready    import assert_node_ready
from .test_04_subscribe     import assert_endelection_event
from .test_06_admin_ipfs    import assert_admin_post_ipfs, assert_subchannels_show_ipfs
from .test_07_post_manifest import cfg_post_manifest_base, assert_post_manifest


@st.composite
def cfg_post_batch(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '07_sub_fetch_records.sh'),
                ('admin', '08_admin_post_batch.sh'),
            ),
        ),
    ])
    return cfg


def assert_post_ceremony(cfg):
    assert_script_logs_match(cfg, 'admin', [
        '^private.*ceremony\\.json$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'POST /api/ceremony/create',
        'POST /api/records/post.*201$',
        'admin posted PublicRecord.*metadata=CeremonyDetails',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'fetched.*CeremonyDetails',
    ])
    assert_script_logs_match(cfg, '(?!admin)', [
        'admin posted CeremonyDetails',
    ])


def assert_advance_phase(cfg, phase: ElectionPhase):
    assert_script_logs_match(cfg, '(?!admin)', [
        f'admin advanced to {str(phase)}$',
    ])
    

@given_cached_tests(
    cfg_strategy = cfg_post_batch(),
    max_examples = 1,
)
def test_post_batch(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
    assert_admin_post_ipfs(cfg)
    assert_subchannels_show_ipfs(cfg)
    assert_post_manifest(cfg)
    assert_post_ceremony(cfg)
    assert_advance_phase(cfg, ElectionConfigPhase(ConfigAnnouncePhase()))
