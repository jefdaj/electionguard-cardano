import fcntl
from contextlib import contextmanager

from .test_config import ResolvedTestConfig


@contextmanager
def lock_test_tmpdir(cfg: ResolvedTestConfig):

    tmpdir_path = cfg.tmpdir_path()
    tmpdir_path.mkdir(parents=True, exist_ok=True)
    lock_path = str(tmpdir_path / 'test.lock')
    
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)   # blocks until acquired
        try:
            yield tmpdir_path
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def init_test_tmpdir(cfg: ResolvedTestConfig):
    tmpdir_path = cfg.tmpdir_path()
    with lock_test_tmpdir(cfg) as lock:

        log_path = tmpdir_path / 'test.log'
        with log_path.open('w') as log: # TODO proper logging
            log.writelines(['init_test_tmpdir start'])

            # init config json
            cfg_path = tmpdir_path / 'test.json'
            if not cfg_path.exists():
                log.writelines(['init_test_tmpdir write config'])
                cfg_path.write_text( cfg.to_json() )

            # init data dirs
            # TODO get container list
            # TODO get dir list
            # TODO create dirs per container
            # TODO chown them to user

            log.writelines(['init_test_tmpdir done'])

    return tmpdir_path
