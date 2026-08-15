from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_05_init_election import *


@st.composite
def cfg_admin_ipfs(draw):
    cfg = draw( config_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '04_subscribe_png.sh'), # TODO subchannels should show admin ipfs
                ('admin', '06_admin_ipfs.sh'),
            ),
        ),
    ])
    return cfg


def assert_admin_ipfs(cfg):
    raise NotImplementedError


@given_cached_tests(
    cfg_strategy = cfg_admin_ipfs(),
    max_examples = 1,
)
def test_admin_ipfs(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
    assert_admin_ipfs(cfg)
#     assert_script_logs_match(cfg, 'admin', [
#         'CH_STR=admin$',
#         'egc collateral await$',
#         'egc election burntesttokens$',
#         'egc collateral return$',
#         'exit 0$'
#     ])
#     assert_node_logs_match(cfg, 'admin', [
#         'minted admin channel STT',
#         'deployed contract',
#         'saved contract details',
#         'Subscribe to this election with',
#         '^egc:election:4:',
#         'Started observer',
#     ])
#     assert_script_logs_match(cfg, '(?!admin)', [
#         '^[0-9]{9,}\\s.*ended election'
#     ])
