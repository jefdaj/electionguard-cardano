from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_04_subscribe     import assert_election_events
from .test_07_post_manifest import cfg_post_manifest_base
from .test_08_post_batch    import assert_advance_phase


@st.composite
def cfg_subs_post_ipfs(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '11_sub_post_ipfs.sh'),
                ('admin', '11_admin_watch_ipfs.sh'),
            ),
        ),
    ])
    return cfg


@given_cached_tests(cfg_strategy=cfg_subs_post_ipfs(), max_examples=1)
def test_subs_post_ipfs(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    # assert_script_logs_match(cfg, 'admin', [
        # 'CH_STR=admin$',
        # 'egc collateral await$',
        # '^private.*manifest\\.json$',
    # ])
    # assert_node_logs_match(cfg, '.*', [

        # TODO get this working reliably... maybe wait longer? tweak ipfs?
        # 'fetched.*CeremonyDetails',

    # ])
    # assert_node_logs_match(cfg, 'admin', [
        # 'GET /api/channel/await\\?role=admin',
        # 'GET /api/collateral/await',
        # 'POST /api/ceremony/create',
        # 'POST /api/records/post.*201$',
        # 'admin posted PublicRecord.*metadata=Manifest',
    # ])
    # assert_script_logs_match(cfg, '(?!admin)', [
        # 'admin posted Manifest',
        # '^[0-9]{9,}\\s.*ended election',
    # ])
