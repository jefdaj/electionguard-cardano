from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_04_subscribe     import assert_election_events
from .test_05_init_election import cfg_init_election_base


@st.composite
def cfg_post_manifest_base(draw):
    cfg = draw( cfg_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(name = 'install_node_cfgs', args = ()),
    ])
    return cfg


@st.composite
def cfg_post_manifest(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '07_sub_fetch_records.sh'),
                ('admin', '07_admin_post_manifest.sh'),
            ),
        ),
    ])
    return cfg


def assert_post_manifest(cfg):
    assert_script_logs_match(cfg, 'admin', [
        '^private.*manifest\\.json$',
    ])
    assert_node_logs_match(cfg, 'admin', [
        'POST /api/manifest .*201$',
        'POST /api/records/post.*201$',
        'admin posted PublicRecord.*metadata=Manifest',
        'fetched.*Manifest',
    ])
    assert_script_logs_match(cfg, '(?!admin)', [
        'admin posted Manifest',
    ])


@given_cached_tests(
    cfg_strategy = cfg_post_manifest(),
    max_examples = 1,
)
def test_post_manifest(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_election_events(cfg)
    assert_post_manifest(cfg)
