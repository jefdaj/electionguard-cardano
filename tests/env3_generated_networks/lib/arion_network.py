import pytest
import subprocess
import time
import os
import signal
from pathlib import Path
from contextlib import contextmanager
from egc import *
from ..lib.config import ResolvedTestConfig
from tests.lib.py_utils import raise_on_signals

def arion_subprocess_kwargs(cfg: ResolvedTestConfig, arion_dir: Path) -> dict:
    """Factor out the common kwargs that are required for arion up/down to work
    with generated compose files."""
    tmpdir_path = cfg.tmpdir_path()
    arion_env = os.environ.copy()
    arion_env['EGC_TEST_JSON'] = str(tmpdir_path / 'test.json')
    assert 'EGC_CARDANO_DIR' in arion_env.keys() # set in flake.nix
    return {
        'cwd': str(arion_dir),
        'env': arion_env,
    }

def run_arion(
    cfg: ResolvedTestConfig,
    arion_dir: Path,
    arion_args: list[str],
    log_handle,
):
    "Run global arion commands like up and down."
    kwargs = arion_subprocess_kwargs(cfg, arion_dir)
    cmd = ["arion"] + arion_args

    return subprocess.run(
        cmd,
        check=True,
        stdout=log_handle,
        stderr=subprocess.STDOUT,  # stderr goes to the same file as stdout
        **kwargs,
    )

def run_arion_down(cfg: ResolvedTestConfig, arion_dir: Path, log_handle):
    # TODO --rmi local? all?
    run_arion(cfg, arion_dir, ['down', '--remove-orphans', '--volumes'], log_handle)

def run_arion_up(cfg: ResolvedTestConfig, arion_dir: Path, log_handle):
    run_arion_down(cfg, arion_dir, log_handle) # in case of messy prev run
    run_arion(cfg, arion_dir, ['up', '-d'], log_handle)
    time.sleep(10) # TODO remove?


# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
# TODO no tmp_root, just resolved cfg which should include that
# @pytest.fixture(scope='function') # TODO does it need to be narrow for the cfg to appear?
@contextmanager
def arion_network_up(cfg: ResolvedTestConfig, arion_dir: Path):
    log_path = cfg.log_path()
    with log_path.open('w') as log_handle: # TODO proper logging
        def log(msg):
            log_handle.writelines([msg + '\n'])
            log_handle.flush()
        log('arion_network_up start')

        with raise_on_signals(signal.SIGTERM, signal.SIGINT):
            run_arion_up(cfg, arion_dir, log_handle)
            try:
                log('arion_network_up yield')
                yield cfg.arion_project_name() # TODO or parse arion cat /docker inspect? or None?
            finally:
                log('arion_network_up finally')
                run_arion_down(cfg, arion_dir, log_handle)
