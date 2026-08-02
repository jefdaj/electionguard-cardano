from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

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

@given_cached_tests(
    cfg_strategy = config_init_election,
    max_examples = 3,
)
def test_init_election(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, 'admin', 'egc collateral return$')
    assert_script_logs_match(cfg, 'admin', 'exit 0$')
    assert_script_logs_match(cfg, '(?!admin)', '^[0-9]{9,}\\s.*ended election')
    assert_script_logs_do_not_match(cfg, '.*', '^arion: FatalError')
