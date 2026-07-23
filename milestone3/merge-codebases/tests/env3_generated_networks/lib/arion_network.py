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

# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
# TODO no tmp_root, just resolved cfg which should include that
# @pytest.fixture(scope='function') # TODO does it need to be narrow for the cfg to appear?
@contextmanager
def arion_network_up(arion_dir: Path, test_cfg: ResolvedTestConfig):

    arion_env = os.environ.copy()
    tmpdir_path = test_cfg.tmpdir_path()
    arion_env['EGC_TEST_JSON'] = tmpdir_path / 'test.json'
    assert 'EGC_CARDANO_DIR' in arion_env.keys() # set in flake.nix

    log_path = tmpdir_path / 'test.log'
    with log_path.open('w') as log_handle: # TODO proper logging
        def log(msg):
            log_handle.writelines([msg + '\n'])
            log_handle.flush()
        log('arion_network_up start')

        def run_arion(args: list[str]):
            return subprocess.run(
                ["arion"] + args,
                cwd   = arion_dir, # where to look for arion-{pkgs,compose}.nix
                env   = arion_env, # with env vars loaded by arion-compose.nix
                check = True
            )

        with raise_on_signals(signal.SIGTERM, signal.SIGINT):
            run_arion(["down", "--remove-orphans", "--volumes"]) # in case of leftovers from prev run
            run_arion(["up", "-d"])
            time.sleep(20) # TODO how long is actually needed?
            try:
                log('arion_network_up yield')
                yield test_cfg.arion_project_name() # TODO or parse arion cat /docker inspect? or None?
            finally:
                log('arion_network_up finally')
                run_arion(["down", "--remove-orphans", "--volumes"])
                time.sleep(5) # TODO remove?

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
