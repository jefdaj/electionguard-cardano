from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *
from ..lib.py_utils import deep_replace

@st.composite
def config_init_election(draw):
    cfg = draw( hashed_test_config() )
    fn_name = sys._getframe().f_code.co_name
    cfg = deep_replace(
        cfg,
        'pytest.config_fns.names',
        tuple(list(cfg.pytest.config_fns.names) + [fn_name])
    )
    cfg = deep_replace(
        cfg,
        'pytest.setup_fns',
        SetupFnsConfig(fns=(
            FnCallConfig(
                name = 'render_egc_scripts',
                args = (
                    ('default', 'subscribe-qr-png.sh'), # admin creates qrcode now
                    ('admin', 'init-election.sh'),
                ),
            ),
        )),
    )
    return cfg

# @given_cached_tests(
#     cfg_strategy = config_init_election,
#     max_examples = 1,
# )
# def test_init_election(cfg: ResolvedTestConfig):
#     assert_node_logs_do_not_match(cfg=cfg, pattern='^arion: FatalError')
