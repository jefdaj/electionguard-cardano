import pytest
from egc import *
from ..lib import *
from .lib  import *

# TODO rename the base config?
@given_cached_tests(hashed_test_config, max_examples=3)
def test_cleanup_called(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg=cfg, pattern='^cleaning up$')
