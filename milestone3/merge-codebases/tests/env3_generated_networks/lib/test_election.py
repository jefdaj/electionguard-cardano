import os
import time
from contextlib import contextmanager
from pathlib import Path
from .test_config import HashedTestConfig, ResolvedTestConfig
from .arion_network import arion_network_up

# def run_test_election(cfg: HashedTestConfig, arion_dir: Path, tmp_root: Path) -> Path:
@contextmanager
def run_test_election(cfg: ResolvedTestConfig) -> Path:
    "Run the election if needed, and return the tmpdir path."

    # resolved_cfg = ResolvedTestConfig.from_config(cfg, tmp_root)
    tmpdir_path = cfg.tmpdir_path()
    cfg_path  = cfg.cfg_path()
    lock_path = cfg.lock_path()
    log_path  = cfg.log_path()

    # if cfg_path.exists():
    # If another instance is running, wait for it to finish first.
    while lock_path.exists():
        time.sleep(1)
        # yield tmpdir_path

    # Now check if it finished running the election. If not, that could be
    # because it was a simpler test, or because something failed.

    else:
        try:
            # TODO this goes in init_test_tmpdir
            # tmpdir_path.mkdir(parents=True, exist_ok=True)

            # lock = lock_path.open('w')

            # TODO create arion bind mount dirs here too
            # TODO and chown them if needed

            # cfg_path.write_text( resolved_cfg.to_json() )

            # TODO run election here
            # TODO or should that be something else that uses the contextmanager?
            # main(cfg, log)

            with arion_network_up(arion_dir=arion_dir, test_cfg=resolved_cfg) as network_prefix:
                yield tmpdir_path

        finally:
            try:
                lock.close()
            except:
                pass
            lock_path.unlink(missing_ok=True)
