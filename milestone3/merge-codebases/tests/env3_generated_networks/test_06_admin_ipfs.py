from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_create_wallet import assert_wallet_created
from .test_03_node_ready import assert_node_ready
from .test_04_subscribe import assert_endelection_event
from .test_05_init_election import cfg_init_election_base


@st.composite
def cfg_admin_post_ipfs(draw):
    cfg = draw( cfg_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '06_subchannel_show_ipfs.sh'),
                ('admin', '06_admin_post_ipfs.sh'),
            ),
        ),
    ])
    return cfg


def assert_admin_post_ipfs(cfg):
    assert_script_logs_match(cfg, 'admin', [
        'egc ipfs post$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'PUT /api/ipfs.*201$',
        'skip peering with own node',
    ])

def assert_subchannels_show_ipfs(cfg):
    assert_script_logs_match(cfg, '(?!admin)', [
        'admin posted ipfs peerid',
        '"peer_id": "12D',
    ])
    assert_node_logs_match(cfg, '(?!admin)', [
        'GET /api/ipfs.*200',
    ])


@given_cached_tests(
    cfg_strategy = cfg_admin_post_ipfs(),
    max_examples = 1,
)
def test_admin_post_ipfs(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_wallet_created(cfg)
    assert_node_ready(cfg)
    assert_endelection_event(cfg)
    assert_admin_post_ipfs(cfg)
    assert_subchannels_show_ipfs(cfg)
