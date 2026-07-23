import fcntl
from contextlib import contextmanager

from .test_config import ResolvedTestConfig


@contextmanager
def lock_test_tmpdir(cfg: ResolvedTestConfig):

    tmpdir_path = cfg.tmpdir_path()
    tmpdir_path.mkdir(parents=True, exist_ok=True)
    lock_path = tmpdir_path / 'test.lock'
    
    with lock_path.open("w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)   # blocks until acquired
        try:
            yield tmpdir_path
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
            lock_path.unlink(missing_ok=True)


def init_test_tmpdir(cfg: ResolvedTestConfig):
    tmpdir_path = cfg.tmpdir_path()
    with lock_test_tmpdir(cfg) as lock:

        log_path = tmpdir_path / 'test.log'
        with log_path.open('w') as log_handle: # TODO proper logging
            log = lambda msg: log_handle.writelines([msg + '\n'])
            log('init_test_tmpdir start')

            # init config json
            cfg_path = tmpdir_path / 'test.json'
            if not cfg_path.exists():
                log('init_test_tmpdir write config')
                cfg_path.write_text( cfg.to_json() )

            # init data dirs
            log('init_test_tmpdir make bind dirs')
            for relpath in cfg.bind_dirs():
                d = tmpdir_path / relpath
                d.mkdir(parents=True, exist_ok=True)

            log('init_test_tmpdir done')

    return tmpdir_path
