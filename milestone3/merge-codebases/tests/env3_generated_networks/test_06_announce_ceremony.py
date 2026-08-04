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
                ('admin', 'announce-ceremony.sh'), # TODO write this
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
    max_examples = 1,
)
def test_announce_ceremony(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, 'admin', [
        'CH_STR=admin$',
        'egc collateral await$',
        'egc election burntesttokens$',
        'egc collateral return$',
        'exit 0$'
    ])
    assert_node_logs_match(cfg, 'admin', [
        'minted admin channel STT',
        'deployed contract',
        'saved contract details',
        'Subscribe to this election with',
    ])
    assert_script_logs_match(cfg, '(?!admin)', ['^[0-9]{9,}\\s.*ended election'])
    assert_script_logs_do_not_match(cfg, '.*', ['^Traceback', '^arion: FatalError'])
