from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

@st.composite
def cfg_batch_manifest(draw):
    cfg = draw( config_init_election_base() )
    cfg = append_config_fn_name(cfg)
    cfg = replace_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('default', 'subscribe-qr-png.sh'),
                ('admin', '08_batch_manifest.sh'),
            ),
        ),
    ])
    return cfg


@given_cached_tests(
    cfg_strategy = cfg_batch_manifest(),
    max_examples = 1,
)
def test_batch_manifest(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
#     assert_script_logs_match(cfg, 'admin', [
#         'CH_STR=admin$',
#         'egc collateral await$',
#         '^private.*manifest\\.json$',
#     ])
#     assert_node_logs_match(cfg, '.*', [
# 
#         # TODO get this working reliably... maybe wait longer? tweak ipfs?
#         # 'fetched.*CeremonyDetails',
# 
#     ])
#     assert_node_logs_match(cfg, 'admin', [
#         'GET /api/channel/await\\?role=admin',
#         'GET /api/collateral/await',
#         'POST /api/ceremony/create',
#         'POST /api/records/post.*201$',
#         'admin posted PublicRecord.*metadata=Manifest',
#     ])
#     assert_script_logs_match(cfg, '(?!admin)', [
#         'admin posted Manifest',
#         '^[0-9]{9,}\\s.*ended election',
#     ])
