import functools, inspect
from typing import Callable
from hypothesis import given, settings, seed, Phase
from hypothesis import strategies as st
from pathlib import Path

from .random_seed   import get_random_seed
from .arion_network import arion_network_up
from .egc_scripts   import run_egc_scripts
from .test_config   import resolve_test_config, hashed_test_config, HashedTestConfig, ResolvedTestConfig
from .test_tmpdir   import init_test_tmpdir, lock_test_tmpdir

from .setup_fns import run_setup_fns

# TODO move to py_utils
def silent_yad(decorators):
    """Based on 'yet another decorator': https://stackoverflow.com/a/4122845
    But also adds this wrapped/sig stuff to prevent pytest "collection from a
    different file" arrows cluttering test output."""
    def decorator(f):
        wrapped = f
        for d in reversed(decorators):
            wrapped = d(wrapped)
        # capture real signature (outermost) before re-pointing
        sig = inspect.signature(wrapped)
        functools.wraps(f)(wrapped) # location: __wrapped__ -> f
        wrapped.__signature__ = sig # fixtures: honor outer params
        return wrapped
    return decorator

def run_egc_scripts_cached(
        cfg: HashedTestConfig,
        tmp_root: Path,
        env3_arion_dir: Path,
    ) -> ResolvedTestConfig:
    rcfg = resolve_test_config(cfg=cfg, tmp_root=tmp_root)
    with lock_test_tmpdir(cfg=rcfg) as test_tmpdir:
        log_path = test_tmpdir / 'script.log'
        if not log_path.exists():
            # the test hasn't been run already
            init_test_tmpdir(cfg=rcfg)
            run_setup_fns(cfg=rcfg)
            with arion_network_up(cfg=rcfg, arion_dir=env3_arion_dir):
                run_egc_scripts(cfg=rcfg, arion_dir=env3_arion_dir)
    return rcfg

def prerun_egc_scripts(final_test_fn_from_rcfg):
    def fn_from_fixtures(cfg: HashedTestConfig, tmp_root: Path, env3_arion_dir: Path):
        rcfg = run_egc_scripts_cached(cfg, tmp_root, env3_arion_dir)
        return final_test_fn_from_rcfg(rcfg)
    return fn_from_fixtures


# A somewhat mind bending hack to make hypothesis reuse cached test elections.
# This way we can define a lot of rapid tests that make individual assertions
# about the results. It's kind of like a hybrid between givens and pytest
# fixtures: we generate the election configs randomly, but then reuse the same
# random values across lots of tests.
#
# TODO is this a partial solution to https://github.com/HypothesisWorks/hypothesis/issues/114
def given_cached_tests(
        cfg_strategy = hashed_test_config,
        max_examples = 10,
    ):
    return silent_yad([
        seed(get_random_seed()),
        settings(
            max_examples = max_examples,
            deadline = None, # TODO set a long one?
            phases = (Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink),
            # database defaults on -> failing configs replay next run
            # TODO derandomize  = False,?
        ),
        given(cfg = cfg_strategy()),
        prerun_egc_scripts,
    ])
