from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_03_node_ready import assert_node_ready
from .test_04_subscribe import *


@st.composite
def cfg_init_election_base(draw):
    cfg = draw( config_test_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'install_funder_sk',
            args = ()
        ),
    ])
    return cfg
 

@st.composite
def cfg_init_election(draw):
    cfg = draw( config_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '04_subscribe_png.sh'), # TODO separate script?
                ('admin', '05_init_election.sh'),
            ),
        ),
    ])
    return cfg


@given_cached_tests(
    cfg_strategy = cfg_init_election(),
    max_examples = 1,
)
def test_init_election(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
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
    # assert_script_logs_match(cfg, '(?!admin)', [
    #     '^[0-9]{9,}\\s.*ended election'
    # ])
