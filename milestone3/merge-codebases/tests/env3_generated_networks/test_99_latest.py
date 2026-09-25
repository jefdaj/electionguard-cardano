from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

# This "test latest" file is for developing the latest bit of the election
# workflow, whatever that is at a given time. It runs the workflow so far, then
# pauses for manual dev work before the report and cleanup steps in each
# script.

from .test_07_post_manifest import cfg_post_manifest_base


@st.composite
def cfg_latest(draw):
    cfg = draw( cfg_post_manifest_base() )
    cfg = append_config_fn_name(cfg)
    cfg = append_setup_fns(cfg, [
        FnCallConfig(
            name = 'render_egc_scripts',
            args = (
                ('admin',    '99_latest_admin.sh'),
                ('guardian', '99_latest_guardian.sh'),
                ('default',  '99_latest_sub.sh'),
                ('pause_for_dev_work', True),
            ),
        ),
    ])
    return cfg


@given_cached_tests(cfg_strategy=cfg_latest(), max_examples=1)
def test_latest(cfg: ResolvedTestConfig):
    assert_test_completed(cfg)
