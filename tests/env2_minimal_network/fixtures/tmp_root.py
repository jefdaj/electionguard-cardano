import pytest
from pathlib import Path

@pytest.fixture(scope='session')
def env2_tmp_root(request):
    project_root = request.config.rootpath.absolute()
    return project_root / 'data' / 'env2'
