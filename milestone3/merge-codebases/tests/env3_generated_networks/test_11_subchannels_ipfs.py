from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_10_add_subchannels import *


@st.composite
def cfg_subchannels_ipfs(draw):
    cfg = draw( cfg_add_subchannels_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '11_subchannel_post_ipfs.sh'),
                ('admin', '11_admin_watch_ipfs.sh'),
            ),
        ),
    ])
    return cfg


@given_cached_tests(
    cfg_strategy = cfg_subchannels_ipfs(),
    max_examples = 1,
)
def test_subchannels_post_ipfs(cfg: ResolvedTestConfig):
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
