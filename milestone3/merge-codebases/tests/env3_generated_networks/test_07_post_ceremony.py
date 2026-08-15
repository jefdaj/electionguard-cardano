from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_06_admin_ipfs import *


@st.composite
def cfg_post_ceremony_base(draw):
    cfg = draw( cfg_init_election_baes() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(name = 'install_node_cfgs', args = ()),
    ])
    return cfg

@st.composite
def cfg_post_ceremony(draw):
    cfg = draw( cfg_post_ceremony_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', '04_subscribe_png.sh'), # TODO new script that finds in fetched dir
                ('admin', '07_ceremony_post.sh'),
            ),
        ),
    ])
    return cfg


# TODO find and assert from all nodes, not just admin
def assert_post_ceremony(cfg):
    assert_script_logs_match(cfg, 'admin', [
        '^private.*ceremony\\.json$',

        # TODO get this working reliably... maybe wait longer? tweak ipfs?
        # 'fetched.*CeremonyDetails',

    ])
    assert_node_logs_match(cfg, 'admin', [
        'POST /api/ceremony/create',
        'POST /api/records/post.*201$',
        'admin posted PublicRecord.*metadata=CeremonyDetails',
    ])
    assert_script_logs_match(cfg, '(?!admin)', [
        'admin posted CeremonyDetails',
    ])


@given_cached_tests(
    cfg_strategy = cfg_post_ceremony(),
    max_examples = 1,
)
def test_post_ceremony(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
    assert_post_ceremony(cfg)
