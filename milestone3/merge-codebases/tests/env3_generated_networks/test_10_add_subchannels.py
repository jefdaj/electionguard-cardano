from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_07_post_ceremony import *


@st.composite
def cfg_add_subchannels_base(draw):
    cfg = draw( cfg_post_ceremony_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(name='install_n_requests', args=()),
    ])
    return cfg


@st.composite
def cfg_add_subchannels(draw):
    cfg = draw( cfg_add_subchannels_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '10_request_subchannel.sh'),
                ('admin', '10_add_subchannels.sh'),
            ),
        ),
    ])
    return cfg


@given_cached_tests(
    cfg_strategy = cfg_add_subchannels(),
    max_examples = 1,
)
def test_add_subchannels(cfg: ResolvedTestConfig):
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
