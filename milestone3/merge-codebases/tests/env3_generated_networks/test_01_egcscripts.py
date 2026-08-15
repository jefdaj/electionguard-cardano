import pytest
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

@given_cached_tests(config_test_base(), max_examples=3)
def test_cleanup_called(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, '.*', ['^cleaning up$'])
    assert_script_logs_do_not_match(cfg, '.*', [
        '^Traceback',
        '^arion: FatalError',
        '^cleanup failed$'
    ])
