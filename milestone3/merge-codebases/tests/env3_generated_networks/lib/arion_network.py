import pytest
import subprocess
import time
import os
import signal
import re
from pathlib import Path
from contextlib import contextmanager
from egc import *
from ..lib.test_config import ResolvedTestConfig
from tests.lib.py_utils import raise_on_signals
# from ..lib.test_tmpdir import lock_test_tmpdir

def arion_subprocess_kwargs(cfg: ResolvedTestConfig, arion_dir: Path) -> dict:
    """Factor out the common kwargs that are required for arion up/down to work
    with generated compose files."""
    tmpdir_path = cfg.tmpdir_path()
    arion_env = os.environ.copy()
    arion_env['EGC_TEST_JSON'] = tmpdir_path / 'test.json'
    assert 'EGC_CARDANO_DIR' in arion_env.keys() # set in flake.nix
    return {
        'cwd': arion_dir,
        'env': arion_env,
    }

def run_arion(cfg: ResolvedTestConfig, arion_dir: Path, arion_args: list[str]):
    "Run global arion commands like up and down."
    tmpdir_path = cfg.tmpdir_path()
    kwargs = arion_subprocess_kwargs(cfg, arion_dir)
    # log_path = tmpdir_path / 'data' / node_name / 'test.log' # TODO script.log?
    cmd = ["arion"] + arion_args
    return subprocess.run(cmd, check = True, **kwargs)

def run_arion_down(cfg: ResolvedTestConfig, arion_dir: Path):
    # TODO --rmi local? all?
    run_arion(cfg, arion_dir, ['down', '--remove-orphans', '--volumes'])

def run_arion_up(cfg: ResolvedTestConfig, arion_dir: Path):
    run_arion_down(cfg, arion_dir) # in case of messy prev run
    run_arion(cfg, arion_dir, ['up', '-d'])
    time.sleep(3)


# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
# TODO no tmp_root, just resolved cfg which should include that
# @pytest.fixture(scope='function') # TODO does it need to be narrow for the cfg to appear?
@contextmanager
def arion_network_up(cfg: ResolvedTestConfig, arion_dir: Path):
    tmpdir_path = cfg.tmpdir_path()
    log_path = tmpdir_path / 'test.log'
    with log_path.open('w') as log_handle: # TODO proper logging
        def log(msg):
            log_handle.writelines([msg + '\n'])
            log_handle.flush()
        log('arion_network_up start')

        with raise_on_signals(signal.SIGTERM, signal.SIGINT):
            run_arion_up(cfg, arion_dir)
            try:
                log('arion_network_up yield')
                yield cfg.arion_project_name() # TODO or parse arion cat /docker inspect? or None?
            finally:
                log('arion_network_up finally')
                run_arion_down(cfg, arion_dir)

def assert_node_logs_match(cfg: ResolvedTestConfig, pattern: str):
    "Assert at least one line in each node's test.log matches `pattern`."
    rx = re.compile(pattern)
    tmpdir_path = cfg.tmpdir_path()
    log_paths = [
        tmpdir_path / 'data' / name / 'egc' / 'test.log'
        for name in cfg.node_names()
    ]
    for log_path in log_paths:
        with log_path.open('r') as f:
            lines = [l.rstrip('\n') for l in f.readlines()]
        print(f'lines: {lines}')
        print(f'rx: {rx}')
        print(f'rx.pattern: {rx.pattern}')
        assert any(rx.search(l) for l in lines), f"{p} had no line matching {rx.pattern!r}"
