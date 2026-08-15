from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

# TODO derive this from config_announce_ceremony instead (need a replace egc script fn)
@st.composite
def config_add_subchannels(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', 'request-subchannel.sh'),
                ('admin', 'add-subchannels.sh'),
            ),
        ),
        FnCallConfig(name='install_funder_sk' , args=()),
        FnCallConfig(name='install_node_cfgs' , args=()),
        FnCallConfig(name='install_n_requests', args=()),
    ])
    return cfg

ADD_SUBCHANNELS_CONFIGS = [f() for f in [
    config_add_subchannels,
]]


@given_cached_tests(
    cfg_strategy = st.one_of(ADD_SUBCHANNELS_CONFIGS),
    max_examples = 1,
)
def test_add_subchannels(cfg: ResolvedTestConfig):
    assert_script_logs_do_not_match(cfg, '.*', [
        'Traceback',
        'arion: FatalError',
        'Command not available from current role',
    ])
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
