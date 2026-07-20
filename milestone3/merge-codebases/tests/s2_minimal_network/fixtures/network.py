import pytest
import subprocess
import time
from pathlib import Path
from tests.helpers import per_network_fixture
from egc import *

# TODO alias for package scope to match the others

# TODO what should this yield, if anything?
# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
@per_network_fixture
def arion_network(request):
    compose_dir = Path(request.fspath).parent # dir of the calling conftest
    subprocess.run(["arion", "up", "-d"], cwd=compose_dir, check=True)
    time.sleep(20) # TODO remove?
    try:
        yield compose_dir # TODO or parse arion cat /docker inspect? or None?
    finally:
        subprocess.run(["arion", "down"], cwd=compose_dir, check=True)

@per_network_fixture
def ogmios(arion_network) -> OgmiosV6ChainContext:
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

# TODO what should this return, if anything?
@per_network_fixture
def ipfs(arion_network):
    ipfs_wait_until_stable_sync()
    return
