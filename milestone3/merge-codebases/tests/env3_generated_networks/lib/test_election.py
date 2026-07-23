import os
from pathlib import Path
import time

# from tests.lib import *
# from .lib import *

from .test_config import HashedTestConfig, ResolvedTestConfig

# # def hash_config(cfg: RunJson, truncate=99) -> (int, str):
# #     "Ensures tmpdirs are not being reused after their configs change."
# #     s = str(cfg).encode('utf-8')
# #     h = hashlib.md5(s).digest().hex()
# #     int_hash = int(str(int(h, 16))[-truncate:])
# #     str_hash = h[:truncate]
# #     return (int_hash, str_hash)
# 
# 
# TODO better name? testdir, tmpdir both taken(!) by built-in fixtures
def run_test_election(cfg: HashedTestConfig, tmp_root: Path) -> Path:
    "Run the election if needed, and return the tmpdir path."

    resolved_cfg = ResolvedTestConfig.from_hashed_config(cfg)
    # tmpdir_path  = tmp_root / ('test' + str(resolved_cfg.cache_key))
    tmpdir_path = resolved_cfg.tmpdir_path(tmp_root)
    cfg_path  = tmpdir_path / 'test.json'
    lock_path = tmpdir_path / 'test.lock'
    log_path  = tmpdir_path / 'test.log' # TODO can this also be used for the lock?

    # write config

    # use our own custom tmpdir instead of TemporaryDirectory
    # Note this is a different random seed from the fixture of the same name.
    # This one should be derived from that one though, assuming that one was
    # used to generate the runconfig.
    # (random_seed, h5) = hash_config(cfg, truncate=5)
    # test_name = f'test{h5}'
    # tmpdir = test_dir / test_name

    # This should prevent more than one run_test_election from running with the
    # same config at the same time. Not sure whether that happens in practice,
    # but better to be safe than sorry when using pytest -n<threads>, right?
    # TODO why is it making only one election run at a time though?
    # lockfile = tmpdir / 'election.lock'

    # if exists(tmpdir):
    if tmpdir_path.exists():
        # if another instance is running, wait for it to finish
        # TODO proper way to do this?
        while True:
            time.sleep(1)
            if not lock_path.exists():
                break
        yield tmpdir_path # TODO return?

    else:
        try:
            tmpdir_path.mkdir(parents=True, exist_ok=True)
            lock = lock_path.open('w')

            # data_dir = tmpdir / cfg['arion']['data_dir']
            # logfile  = tmpdir / 'election.log'

            # os.makedirs(data_dir, exist_ok=False) # TODO remove?
            # TODO chown to user here?

            # TODO leave data_dir as 'data' and resolve inside election.py?
            # cfg['arion']['data_dir'] = data_dir # TODO absolute?
            # cfg['arion']['project_name'] = test_name

            # cfg_path = tmpdir / 'election.json' # TODO rename?
            # with open(cfg_path, 'w') as f:
            #     json.dump(cfg, f, indent=2)

            # with cfg_path.open('w') as f:
                # json.dump(asdict(cfg), f, indent=2) # TODO sort_keys?
            cfg_path.write_text( resolved_cfg.to_json() )

            # cfg = parse_config(cfg_path, random_seed=random_seed)
            # log = init_log(cfg, logfile, logging.INFO)
            # log.info(f'using random_seed from config hash: {random_seed}\n')

            # TODO where should this live?
            # main(cfg, log)

            yield tmpdir

        finally:
            # TODO rm here? or do we want to keep + inspect the error files?
            # shutil.rmtree(tmpdir, ignore_errors=True)
            # raise
            try:
                lock.close()
            except:
                pass
            lock.rm()
