import pytest
from egc import *
from pathlib import Path
import os
import tempfile
import shutil

# TODO document this
@pytest.fixture(scope="package")
def keys_dir():
    keep = os.environ.get("EGC_KEEP_KEYS", "").lower() in ("1", "true", "yes")
    override = os.environ.get("EGC_KEYS_DIR")

    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        yield path
        return  # never delete a user-supplied dir

    path = Path(tempfile.mkdtemp(prefix="egc-test-keys-"))
    try:
        yield path
    finally:
        if not keep:
            shutil.rmtree(path, ignore_errors=True)
        else:
            print(f"\n[keypair_dir] Preserved at: {path}")

@pytest.fixture(scope='session')
def funder_keys() -> KeyPair:
    kp = KeyPair(name='dev', verbose=False) # leave default, global keys_dir
    return kp

@pytest.fixture(scope='package')
def admin_keys(keys_dir: Path) -> KeyPair:
    kp = KeyPair(keys_dir=keys_dir, name='admin', verbose=False)
    return kp
