from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_04_subscribe     import assert_election_events
from .test_07_post_manifest import cfg_post_manifest_base
from .test_08_post_batch    import assert_advance_phase


@st.composite
def cfg_subs_post_ipfs(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '11_sub_post_ipfs.sh'),
                ('admin', '11_admin_watch_ipfs.sh'),
            ),
        ),
    ])
    return cfg


def assert_peer_id_posted(cfg, node_name: str):
    assert_script_logs_match(cfg, '.*', [
        f'{node_name} posted ipfs peer_id',
        f'"{node_name}": ."peer_id": "12D3Koo',
    ])


def assert_all_peer_ids_posted(cfg):
    assert_script_logs_match(cfg, 'admin', ['^all peer_ids on chain$'])
    for n in cfg.node_names():
        assert_peer_id_posted(cfg, n)


@given_cached_tests(cfg_strategy=cfg_subs_post_ipfs(), max_examples=5)
def test_subs_post_ipfs(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_all_peer_ids_posted(cfg)
