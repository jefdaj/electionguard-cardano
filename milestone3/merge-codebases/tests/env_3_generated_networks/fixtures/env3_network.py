import pytest
import os
import subprocess
import time
from pathlib import Path
from tests.env_3_generated_networks.helpers import *
from egc import *


def parse_config(cfg_path, pause_to_explain, random_seed):
    "Load JSON config and elaborate it a bit."
    cfg_path = realpath(cfg_path)
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
    cfg.project_config = cfg_path # for passing to arion as an env var
    cfg.random_seed = random_seed
    cfg.pause_to_explain = pause_to_explain
    # TODO do something like this per contest answers dict?
    # cfg.votes = dict(cfg.votes) # TODO is this the simplest way to enable iteration?
    ecfg = cfg.election
    ecfg.guardians.sequence_order = [*range(1, ecfg.guardians.count + 1)]
    ecfg.guardians.ids = [f"guardian_{i}" for i in ecfg.guardians.sequence_order]
    return cfg


# TODO alias for package scope to match the others?

# TODO depend on network config here
# TODO yield network name here for use in api addrs?
# TODO how to force arion down on pytest exceptions, keyboardinturrupt etc?
@per_network_fixture
def arion_network(request, env3_tmpdir: Path):
    compose_dir = Path(request.fspath).parent # dir of the calling conftest
    arion_env = os.environ.copy()
    arion_env['EGC_ELECTION_JSON'] = str(env3_tmpdir) / 'election.json' # TODO pass directly?
    subprocess.run(["arion", "up", "-d"], cwd=compose_dir, check=True)
    # time.sleep(20) # TODO remove?
    try:
        yield compose_dir # TODO or parse arion cat /docker inspect? or None?
    finally:
        subprocess.run(["arion", "down"], cwd=compose_dir, check=True)

# TODO get name of arion network here, and use it to return api addr
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

# TODO get name of arion network here, and use it to return api addr
@per_network_fixture
def ipfs(arion_network):
    ipfs_wait_until_stable_sync()
    return
