import pytest
from pathlib import Path

@pytest.fixture(scope='session')
def tmp_root(request):
    project_root = request.config.rootpath.absolute()
    return project_root / 'data'
