import pytest
from hypothesis import given, settings, seed, Phase
from pathlib import Path

from egc   import *
from ..lib import *
from .lib import *

@seed(get_random_seed())
@settings(
    max_examples=25,
    deadline=None,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),  # reuse+shrink back ON
    # database defaults on -> failing configs replay next run
)
@given(cfg=hashed_test_config())
def test_init_tmpdir(env3_arion_dir: Path, tmp_root: Path, cfg: HashedTestConfig):
    resolved_cfg = resolve_test_config(cfg=cfg, tmp_root=tmp_root)
    test_tmpdir = init_test_tmpdir(cfg=resolved_cfg)
    print(f'test_tmpdir: {test_tmpdir}')
