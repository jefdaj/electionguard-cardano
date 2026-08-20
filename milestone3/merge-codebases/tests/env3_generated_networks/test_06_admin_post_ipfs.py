from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_04_subscribe     import assert_election_events
from .test_05_init_election import cfg_init_election_base


@st.composite
def cfg_admin_post_ipfs(draw):
    cfg = draw( cfg_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '06_sub_show_ipfs.sh'),
                ('admin', '06_admin_post_ipfs.sh'),
            ),
        ),
    ])
    return cfg


def assert_admin_post_ipfs(cfg):
    assert_script_logs_match(cfg, 'admin', [
        'egc ipfs post$',
        '"own_node": {"peer_id": "12D3Koo',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'PUT /api/ipfs.*201$',
        'skip peering with own node',
    ])


def assert_subchannels_show_ipfs(cfg):
    assert_script_logs_match(cfg, '(?!admin)', [
        'admin posted ipfs peer_id',
    ])
    assert_node_logs_match(cfg, '(?!admin)', [
        'GET /api/ipfs.*200$',
    ])


@given_cached_tests(cfg_strategy=cfg_admin_post_ipfs(), max_examples=1)
def test_admin_post_ipfs(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_election_events(cfg)
    assert_admin_post_ipfs(cfg)
    assert_subchannels_show_ipfs(cfg)
