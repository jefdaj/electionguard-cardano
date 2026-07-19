import pytest
import subprocess
import time
from pathlib import Path

# TODO rewrite with arion
# TODO scope is ok, right? one for whole 2_minimal_network?
# @pytest.fixture(scope="package")
# @per_election_fixture
@pytest.fixture
def arion_network(request):
    compose_dir = Path(request.fspath).parent # dir of the calling conftest
    subprocess.run(["docker", "compose", "up", "-d"], cwd=compose_dir, check=True)
    time.sleep(20) # TODO remove?
    try:
        yield compose_dir # TODO or parse arion cat /docker inspect? or None?
    finally:
        subprocess.run(["docker", "compose", "down"], cwd=compose_dir, check=True)
