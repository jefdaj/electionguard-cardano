import pytest
from hypothesis import strategies as st
from egc import *
from ..lib import *
from .lib  import *

from .test_02_wallets import WALLET_CONFIGS

CLEANUP_CONFIGS = [f() for f in [
    config_test_base,
]] + WALLET_CONFIGS

# TODO rename the base config?
@given_cached_tests(st.one_of(CLEANUP_CONFIGS), max_examples=3)
def test_cleanup_called(cfg: ResolvedTestConfig):
    assert_script_logs_match(cfg, '.*', ['^cleaning up$'])
    assert_script_logs_do_not_match(cfg, '.*', ['^Traceback', '^arion: FatalError'])
