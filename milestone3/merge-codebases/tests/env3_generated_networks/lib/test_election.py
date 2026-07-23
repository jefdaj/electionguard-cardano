import os
import time
from contextlib import contextmanager
from pathlib import Path
from .test_config import HashedTestConfig, ResolvedTestConfig
from .network import run_arion_network

@contextmanager
def run_test_election(cfg: HashedTestConfig, arion_dir: Path, tmp_root: Path) -> Path:
    "Run the election if needed, and return the tmpdir path."

    resolved_cfg = ResolvedTestConfig.from_hashed_config(cfg, tmp_root)
    tmpdir_path = resolved_cfg.tmpdir_path()
    cfg_path  = tmpdir_path / 'test.json'
    lock_path = tmpdir_path / 'test.lock'
    log_path  = tmpdir_path / 'test.log'

    if cfg_path.exists():
        # If another instance is running, assume it'll handle everything and
        # just wait for it to finish. This generally shouldn't happen though,
        # because the tests are serial.
        while lock_path.exists():
            time.sleep(1)
        yield tmpdir_path

    else:
        try:
            tmpdir_path.mkdir(parents=True, exist_ok=True)
            lock = lock_path.open('w')

            # TODO create arion bind mount dirs here too
            # TODO and chown them if needed

            cfg_path.write_text( resolved_cfg.to_json() )

            # TODO run election here
            # TODO or should that be something else that uses the contextmanager?
            # main(cfg, log)

            with run_arion_network(arion_dir=arion_dir, test_cfg=resolved_cfg) as arion_network:
                yield tmpdir_path

        finally:
            try:
                lock.close()
            except:
                pass
            lock_path.unlink(missing_ok=True)
