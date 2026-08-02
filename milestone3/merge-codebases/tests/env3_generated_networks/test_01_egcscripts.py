import pytest
from egc import *
from ..lib import *
from .lib  import *

# TODO rename the base config?
@given_cached_tests(config_test_base, max_examples=3)
def test_cleanup_called(cfg: ResolvedTestConfig):
    assert_node_logs_match(cfg, '.*', '^cleaning up$')
    assert_node_logs_do_not_match(cfg, '.*', '^arion: FatalError')
