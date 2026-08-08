from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

@st.composite
def config_announce_ceremony(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', 'subscribe-qr-png.sh'), # admin creates qrcode now
                ('admin', 'announce-ceremony.sh'),
            ),
        ),
        FnCallConfig(
            name = 'install_funder_sk',
            args = ()
        ),
        FnCallConfig(
            name = 'install_node_cfgs',
            args = ()
        ),
    ])
    return cfg

ANNOUNCE_CEREMONY_CONFIGS = [f() for f in [
    config_announce_ceremony,
]]


@given_cached_tests(
    cfg_strategy = st.one_of(ANNOUNCE_CEREMONY_CONFIGS),
    max_examples = 3,
)
def test_announce_ceremony(cfg: ResolvedTestConfig):
    assert_script_logs_do_not_match(cfg, '.*', [
        'Traceback',
        'arion: FatalError',
        'Command not available from current role',
    ])
    assert_script_logs_match(cfg, 'admin', [
        'CH_STR=admin$',
        'egc collateral await$',
        '^private.*ceremony\\.json$',
    ])
    assert_node_logs_match(cfg, '.*', [

        # TODO get this working reliably... maybe wait longer? tweak ipfs?
        # 'fetched.*CeremonyDetails',

    ])
    assert_node_logs_match(cfg, 'admin', [
        'GET /api/channel/await\\?role=admin',
        'GET /api/collateral/await',
        'POST /api/ceremony/create',
        'POST /api/records/post.*201$',
        'admin posted PublicRecord.*metadata=CeremonyDetails',
    ])
    assert_script_logs_match(cfg, '(?!admin)', [
        'admin posted CeremonyDetails',
        '^[0-9]{9,}\\s.*ended election',
    ])
