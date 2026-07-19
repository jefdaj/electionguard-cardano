import pytest
import subprocess
import time
from pathlib import Path
from egc import *

# TODO alias for package scope to match the others

@pytest.fixture(scope='package')
def arion_network(request):
    compose_dir = Path(request.fspath).parent # dir of the calling conftest
    subprocess.run(["arion", "up", "-d"], cwd=compose_dir, check=True)
    time.sleep(20) # TODO remove?
    try:
        yield compose_dir # TODO or parse arion cat /docker inspect? or None?
    finally:
        subprocess.run(["arion", "down"], cwd=compose_dir, check=True)

@pytest.fixture(scope='package')
def ogmios(arion_network) -> OgmiosV6ChainContext:
    ctx = OGMIOS_CTX
    deadline = time.monotonic() + OGMIOS_TIMEOUT_SEC
    while True:
        try:
            health = ogmios_health_sync()
            status = health.get("connectionStatus")
            sync   = health.get("networkSynchronization")
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
