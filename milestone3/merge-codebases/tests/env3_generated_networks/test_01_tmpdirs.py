import pytest
from hypothesis import given, settings, seed, Phase
from pathlib import Path

from egc   import *
from ..lib import *
from .lib  import *

@seed(get_random_seed())
@settings(
    max_examples=25,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=hashed_test_config())
def test_generate_tmpdir(tmp_root: Path, cfg: HashedTestConfig):
    with run_test_election(cfg, tmp_root) as test_tmpdir: # lockfile inside enforces serial
        # assert_verifiers_reject(testdir, [...])
        print(f'test_tmpdir: {test_tmpdir}')
