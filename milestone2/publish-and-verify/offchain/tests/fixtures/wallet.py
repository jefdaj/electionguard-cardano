import pytest
from egc import *
from test_utils import per_election_fixture
from pathlib import Path
import os
import tempfile
import shutil
import logging

LOG = logging.getLogger(__name__)

@per_election_fixture
def keys_dir() -> Path:

    # TODO document this
    custom_keys_dir = os.environ.get("EGC_KEYS")

    if custom_keys_dir:
        path = Path(custom_keys_dir)
        LOG.debug(f'using custom key dir EGC_KEYS = {path}')
        path.mkdir(parents=True, exist_ok=True)
        yield path
        return  # never delete a user-supplied dir

    else:
        path = Path(tempfile.mkdtemp(prefix="egc-test-keys-"))
        LOG.debug(f'EGC_KEYS (temporary) = {path}')

    try:
        yield path
    finally:
        if not IS_TEST and not custom_keys_dir:
            LOG.debug(f'rm EGC_KEYS {path}')
            shutil.rmtree(path, ignore_errors=True)
        else:
            LOG.debug(f'preserve EGC_KEYS {path}')
