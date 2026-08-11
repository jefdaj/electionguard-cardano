import subprocess
import time

from .arion_network import arion_subprocess_kwargs, arion_network_up
from .config        import resolve_test_config, HashedTestConfig, ResolvedTestConfig
from .setup_fns     import run_setup_fns
from .tmpdir        import init_test_tmpdir, lock_test_tmpdir
from hypothesis     import given, settings, seed, Phase
from hypothesis     import strategies as st
from pathlib        import Path
from pathlib        import Path
from typing         import Callable


def run_egc_scripts_cached(
        cfg: HashedTestConfig,
        env3_tmp_root: Path,
        env3_arion_dir: Path,
    ) -> ResolvedTestConfig:
    rcfg = resolve_test_config(cfg=cfg, tmp_root=env3_tmp_root)
    with lock_test_tmpdir(cfg=rcfg):
        log_path = rcfg.log_path()
        if not log_path.exists():
            # the test hasn't been run already
            init_test_tmpdir(cfg=rcfg)
            run_setup_fns(cfg=rcfg)
            with arion_network_up(cfg=rcfg, arion_dir=env3_arion_dir):
                run_egc_scripts(cfg=rcfg, arion_dir=env3_arion_dir)
    return rcfg


def prerun_egc_scripts(final_test_fn_from_rcfg):
    def fn_from_fixtures(cfg: HashedTestConfig, env3_tmp_root: Path, env3_arion_dir: Path):
        rcfg = run_egc_scripts_cached(cfg, env3_tmp_root, env3_arion_dir)
        return final_test_fn_from_rcfg(rcfg)
    return fn_from_fixtures


def run_egc_scripts(cfg: ResolvedTestConfig, arion_dir: Path, timeout=1200):
    """Exec /script.sh in each container and log to logfiles. This can be much
    simpler than the old run_many_in_containers, because it only needs to
    manage one long-running script per node."""

    tmpdir_path = cfg.tmpdir_path()
    procs = {} # node_name -> (proc, log_path)
    node_names = cfg.node_names()
    kwargs = arion_subprocess_kwargs(cfg, arion_dir)
    for node_name in node_names:
        log_path = cfg.private_path(node_name) / 'egc' / 'script.log'
        log_handle = log_path.open('w', buffering=1) # TODO 'a' mode?
        # stdbuf here is to force the log to flush line by line
        service_name = f'{node_name}-egc'
        cmd = ['arion', 'exec', '-T', service_name, '--', 'stdbuf', '-oL', '-eL', '/script.sh']
        p = subprocess.Popen(
            cmd,
            stdout = log_handle,
            stderr = subprocess.STDOUT,
            text = True,
            **kwargs,
        )
        procs[node_name] = (p, log_handle)
    # results = {}
    for node_name, (p, log_handle) in procs.items():
        try:
            p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        finally:
            log_handle.close()
        # results[node_name] = p.returncode
    # TODO ignore error codes? not sure if helpful
    # error_codes = {k:v for k,v in results.items() if v != 0}
    # assert len(error_codes) == 0, f'Script error codes: {error_codes}'
    return
