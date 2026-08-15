from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_06_announce_ceremony import config_announce_ceremony

@st.composite
def config_init_election(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', 'subscribe-qr-png.sh'), # admin creates qrcode now
                ('admin', 'init-election.sh'),
            ),
        ),
        FnCallConfig(
            name = 'install_funder_sk',
            args = ()
        ),
    ])
    return cfg

INIT_ELECTION_CONFIGS = [f() for f in [
    config_init_election,
    config_announce_ceremony,
]]

@given_cached_tests(
    cfg_strategy = st.one_of(INIT_ELECTION_CONFIGS),
    max_examples = 3,
)
def test_init_election(cfg: ResolvedTestConfig):
    assert_script_logs_do_not_match(cfg, '.*', [
        'Traceback',
        'arion: FatalError',
        '^cleanup failed$',
    ])
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
        '^egc:election:4:',
        'Started observer',
    ])
    assert_script_logs_match(cfg, '(?!admin)', [
        '^[0-9]{9,}\\s.*ended election'
    ])
