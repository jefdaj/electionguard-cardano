import os
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import subprocess
from .test_config import ResolvedTestConfig
from .arion_network import arion_subprocess_kwargs


### write scripts ###

TEMPLATES_DIR = Path(__file__).parent / 'templates'

JINJA_ENV = Environment(
    loader = FileSystemLoader(TEMPLATES_DIR),
    trim_blocks = True,
    lstrip_blocks = True,
    keep_trailing_newline = False,
)

def write_egc_scripts(cfg: ResolvedTestConfig):
    tmpdir_path  = cfg.tmpdir_path()
    log_path     = cfg.test_log_path()
    scripts_path = tmpdir_path / 'egc_scripts'

    # TODO any better way than assuming it's locked?
    # with lock_test_tmpdir(cfg) as lock:

    with log_path.open('a') as log_handle: # TODO proper logging
        def log(msg):
            log_handle.writelines([msg + '\n'])
            log_handle.flush()
        log('write_egc_scripts start')

        log(f'write_egc_scripts mkdir {scripts_path}')
        scripts_path.mkdir(parents=True, exist_ok=True)

        # TODO one per index rather just one per role?
        node_cfgs = {
            'admin':    cfg.config.nodes.admin,
            'guardian': cfg.config.nodes.guardians,
            'device':   cfg.config.nodes.devices,
            'verifier': cfg.config.nodes.verifiers,
        }
        for (node_role, node_cfg) in node_cfgs.items():
            template = JINJA_ENV.get_template(node_cfg.template)
            n_nodes = 1 if node_role == 'admin' else node_cfg.count
            for node_index in range(1, n_nodes+1):
                node_name = 'admin' if node_role == 'admin' else f'{node_role}{node_index}'
                out_path = scripts_path / f'{node_name}.sh'
                out_text = template.render(
                    node_name    = node_name,
                    node_role    = node_role,
                    node_index   = node_index,
                    # template_name = template_name,
                    debug_script = True,
                )
                log(f'write_egc_scripts write {out_path}')
                out_path.write_text(out_text)
                os.chmod(out_path, 0o755)

        log('write_egc_scripts done')

    return tmpdir_path


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
        log_path = tmpdir_path / 'data' / node_name / 'egc' / 'script.log'
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
