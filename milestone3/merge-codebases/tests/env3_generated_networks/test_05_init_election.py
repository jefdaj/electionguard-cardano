from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import assert_wallet_created
from .test_03_node_ready    import assert_node_ready
from .test_04_subscribe     import assert_endelection_event


@st.composite
def cfg_init_election_base(draw):
    cfg = draw( cfg_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [

        # For funding the election.
        FnCallConfig(name='install_funder_sk' , args=()),

        # Used to estimate --admin-ada when funding the election,
        # and to wait for the correct number of channel request qrcodes.
        FnCallConfig(name='install_n_subs', args=()),

    ])
    return cfg
 

@st.composite
def cfg_init_election(draw):
    cfg = draw( cfg_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '04_subscribe_png.sh'), # same, but now admin creates qrcode
                ('admin', '05_admin_init_election.sh'),
            ),
        ),
    ])
    return cfg


def assert_admin_initelection(cfg):
    assert_script_logs_match(cfg, 'admin', [
        'CH_STR=admin$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'minted admin channel STT',
        'deployed contract',
        'saved contract details',
        'Subscribe to this election with',
        '^egc:election:4:',
        'Started observer',
     ])


def assert_admin_election_cleanup(cfg):
    assert_script_logs_match(cfg, 'admin', [
        'egc election burntesttokens$',
        'egc collateral return$',
        'exit 0$'
    ])


# TODO remove?
def assert_init_election(cfg):
    assert_admin_initelection(cfg)
    assert_admin_election_cleanup(cfg)


@given_cached_tests(
    cfg_strategy = cfg_init_election(),
    max_examples = 1,
)
def test_init_election(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
    assert_init_election(cfg)
