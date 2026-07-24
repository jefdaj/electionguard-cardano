import pytest
import subprocess
import time
import os
import signal
from pathlib import Path
from contextlib import contextmanager
from egc import *
from ..lib.test_config import ResolvedTestConfig
from tests.lib.py_utils import raise_on_signals
# from ..lib.test_tmpdir import lock_test_tmpdir

def arion_subprocess_kwargs(test_cfg: ResolvedTestConfig, arion_dir: Path) -> dict:
    """Factor out the common kwargs that are required for arion up/down to work
    with generated compose files."""
    tmpdir_path = test_cfg.tmpdir_path()
    arion_env = os.environ.copy()
    arion_env['EGC_TEST_JSON'] = tmpdir_path / 'test.json'
    assert 'EGC_CARDANO_DIR' in arion_env.keys() # set in flake.nix
    return {
        'cwd': arion_dir,
        'env': arion_env,
    }

def run_arion(test_cfg: ResolvedTestConfig, arion_dir: Path, arion_args: list[str]):
    "Run global arion commands like up and down."
    tmpdir_path = test_cfg.tmpdir_path()
    kwargs = arion_subprocess_kwargs(test_cfg, arion_dir)
    # log_path = tmpdir_path / 'data' / node_name / 'test.log' # TODO script.log?
    cmd = ["arion"] + arion_args
    return subprocess.run(cmd, check = True, **kwargs)

def run_arion_down(test_cfg: ResolvedTestConfig, arion_dir: Path):
    run_arion(test_cfg, arion_dir, ['down', '--remove-orphans', '--volumes'])

def run_arion_up(test_cfg: ResolvedTestConfig, arion_dir: Path):
    run_arion_down(test_cfg, arion_dir) # in case of messy prev run
    run_arion(test_cfg, arion_dir, ['up', '-d'])


# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
# TODO no tmp_root, just resolved cfg which should include that
# @pytest.fixture(scope='function') # TODO does it need to be narrow for the cfg to appear?
@contextmanager
def arion_network_up(test_cfg: ResolvedTestConfig, arion_dir: Path):
    tmpdir_path = test_cfg.tmpdir_path()
    log_path = tmpdir_path / 'test.log'
    with log_path.open('w') as log_handle: # TODO proper logging
        def log(msg):
            log_handle.writelines([msg + '\n'])
            log_handle.flush()
        log('arion_network_up start')

        with raise_on_signals(signal.SIGTERM, signal.SIGINT):
            run_arion_up(test_cfg, arion_dir)
            try:
                log('arion_network_up yield')
                yield test_cfg.arion_project_name() # TODO or parse arion cat /docker inspect? or None?
            finally:
                log('arion_network_up finally')
                run_arion_down(test_cfg, arion_dir)

# @pytest.fixture(scope='function')
# def env3_ogmios(env3_arion_network) -> OgmiosV6ChainContext:
#     ctx = OGMIOS_CTX # TODO get from arion_network
#     deadline = time.monotonic() + OGMIOS_TIMEOUT_SEC
#     while True:
#         try:
#             health = ogmios_health_sync()
#             status = health["connectionStatus"]
#             sync   = health["networkSynchronization"]
#         except:
#             status = None
#             sync   = None
#         if status == "connected" and int(sync) == 1:
#             LOG.debug('ogmios connected and synced')
#             LOG.debug(f'ogmios: {ctx}')
#             return ctx
#         if time.monotonic()  >= deadline:
#             raise TimeoutError(f'ogmios not ready after {OGMIOS_TIMEOUT_SEC}s.')
#         time.sleep(OGMIOS_POLL_SEC)
