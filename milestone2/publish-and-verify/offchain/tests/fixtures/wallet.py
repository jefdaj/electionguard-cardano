import pytest
from egc import *
from test_utils import per_election_fixture
from pathlib import Path
import os
import tempfile
import shutil
import logging

LOG = logging.getLogger(__name__)

# TODO document this
@per_election_fixture
def keys_dir():
    keep = os.environ.get("EGC_KEEP_KEYS", "").lower() in ("1", "true", "yes")
    LOG.debug(f'EGC_KEEP_KEYS = {keep}')
    override = os.environ.get("EGC_KEYS_DIR")

    if override:
        path = Path(override)
        LOG.debug(f'EGC_KEYS_DIR = {path}')
        path.mkdir(parents=True, exist_ok=True)
        yield path
        return  # never delete a user-supplied dir

    path = Path(tempfile.mkdtemp(prefix="egc-test-keys-"))
    LOG.debug(f'EGC_KEYS_DIR (default) = {path}')
    try:
        yield path
    finally:
        if not keep:
            LOG.debug(f'rm EGC_KEYS_DIR {path}')
            shutil.rmtree(path, ignore_errors=True)
        else:
            LOG.debug(f'preserve EGC_KEYS_DIR {path}')
            print(f"\n[keypair_dir] Preserved at: {path}")
