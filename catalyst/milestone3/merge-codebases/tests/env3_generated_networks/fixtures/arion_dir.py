import pytest
from pathlib import Path

@pytest.fixture(scope='session')
def env3_arion_dir(request):
    repo_dir = request.config.rootpath.absolute()
    return repo_dir / 'tests' / 'env3_generated_networks'
