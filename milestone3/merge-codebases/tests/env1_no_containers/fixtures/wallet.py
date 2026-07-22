import pytest
from egc import *
# from ..lib import per_election_fixture
from pathlib import Path
import os
import tempfile
import shutil
import logging

LOG = logging.getLogger(__name__)

# @per_election_fixture
@pytest.fixture(scope='module')
def keys_dir() -> Path:

    # TODO document this
    custom_keys_dir = os.environ.get("EGC_KEYS")

    if custom_keys_dir:
        path = Path(custom_keys_dir)
        LOG.warning(f'Custom key dir EGC_KEYS={path}')
        path.mkdir(parents=True, exist_ok=True)
        yield path
        return  # never delete a user-supplied dir

    else:
        path = Path(tempfile.mkdtemp(prefix="egc-test-keys-"))
        LOG.debug(f'EGC_KEYS (temporary) = {path}')

    LOG.info(f'Keys will go in {path}')

    try:
        yield path
    finally:
        if EGC_WALLET_MODE != 'scripted' and not custom_keys_dir:
            shutil.rmtree(path, ignore_errors=True)
            LOG.info(f'Removed keys from {path}')
        else:
            LOG.warning(f'Leaving keys in {path}')
