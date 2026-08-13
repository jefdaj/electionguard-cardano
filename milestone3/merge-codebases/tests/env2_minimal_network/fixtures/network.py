import pytest
import subprocess
import time
from pathlib import Path
from egc import *

# TODO alias for package scope to match the others

# TODO what should this yield, if anything?
# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
@pytest.fixture(scope='session')
def env2_arion_network(request):
    compose_dir = Path(__file__).parent.parent
    # in case of leftovers from a previous run:
    subprocess.run(["arion", "down", "--remove-orphans", "--volumes"], cwd=compose_dir, check=True)
    subprocess.run(["arion", "up", "-d"], cwd=compose_dir, check=True)
    time.sleep(20) # TODO remove?
    try:
        yield compose_dir # TODO or parse arion cat /docker inspect? or None?
    finally:
        subprocess.run(["arion", "down", "--remove-orphans", "--volumes"], cwd=compose_dir, check=False)
        # time.sleep(5) # TODO remove?

@pytest.fixture(scope='session')
def env2_ogmios(env2_arion_network) -> OgmiosV6ChainContext:
    ctx = OGMIOS_CTX
    deadline = time.monotonic() + OGMIOS_TIMEOUT_SEC
    while True:
        try:
            health = ogmios_health_sync()
            status = health["connectionStatus"]
            sync   = health["networkSynchronization"]
        except:
            status = None
            sync   = None
        if status == "connected" and int(sync) == 1:
            LOG.debug('ogmios connected and synced')
            LOG.debug(f'ogmios: {ctx}')
            return ctx
        if time.monotonic()  >= deadline:
            raise TimeoutError(f'ogmios not ready after {OGMIOS_TIMEOUT_SEC}s.')
        time.sleep(OGMIOS_POLL_SEC)

@pytest.fixture(scope='session')
def env2_ipfs(env2_arion_network, env2_tmp_root: Path):
    ipfs_ = IPFSService(
        records_to_post_dir = env2_tmp_root / 'ipfs_fixture' / 'records_to_post',
        records_fetched_dir = env2_tmp_root / 'ipfs_fixture' / 'records_fetched',
    )
    ipfs_.start()
    ipfs_.wait_until_stable_sync()
    return ipfs_
