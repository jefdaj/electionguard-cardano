import time
from pathlib import Path
import subprocess
from .config import ResolvedTestConfig
from .arion_network import arion_subprocess_kwargs


### run scripts ###

def run_egc_scripts(cfg: ResolvedTestConfig, arion_dir: Path, setup_fn, timeout=300):
    """Exec /script.sh in each container and log to logfiles. This can be much
    simpler than the old run_many_in_containers, because it only needs to
    manage one long-running script per node."""

    setup_fn(cfg)
    tmpdir_path = cfg.tmpdir_path()
    procs = {} # node_name -> (proc, log_path)
    node_names = cfg.node_names()
    kwargs = arion_subprocess_kwargs(cfg, arion_dir)
    for node_name in node_names:
        log_path = cfg.egc_path(node_name) / 'script.log'
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
