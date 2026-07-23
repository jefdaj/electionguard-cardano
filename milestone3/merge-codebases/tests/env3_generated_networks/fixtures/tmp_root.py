import pytest
from pathlib import Path

@pytest.fixture(scope='session')
def tmp_root(request):
    project_root = request.config.rootpath
    return project_root / 'data' / 'env3' # TODO what should this actually be called?
