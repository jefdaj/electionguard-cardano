import pytest

@pytest.fixture(scope='session')
def tmp_root(request):
    repo_dir = Path(request.fspath).parents[2] # TODO how many parents?
    return repo_dir / 'data' / 'env3' # TODO what should this actually be called?
