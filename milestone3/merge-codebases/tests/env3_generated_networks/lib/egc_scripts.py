import os
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
    keep_trailing_newline = True,
)

def write_egc_scripts(cfg: ResolvedTestConfig):
    tmpdir_path  = cfg.tmpdir_path()
    scripts_path = tmpdir_path / 'egc_scripts'
    log_path     = tmpdir_path / 'test.log'

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
        template_names = {
            'admin':    cfg.config.nodes.admin.script,
            'guardian': cfg.config.nodes.guardians.script,
            'device':   cfg.config.nodes.devices.script,
            'verifier': cfg.config.nodes.verifiers.script,
        }
        for (role, template_name) in template_names.items():
            template = JINJA_ENV.get_template(template_name)
            out_path = scripts_path / (role + '.sh')
            out_text = template.render(
                role = role,
                template_name = template_name,
                debug = False, # only a personal convention
            )
            log(f'write_egc_scripts write {out_path}')
            out_path.write_text(out_text)
            os.chmod(out_path, 0o755)

        log('write_egc_scripts done')

    return tmpdir_path


### run scripts ###

def run_egc_scripts(test_cfg: ResolvedTestConfig, arion_dir: Path, timeout=300):
    """Exec /script.sh in each container and log to logfiles. This can be much
    simpler than the old run_many_in_containers, because it only needs to
    manage one long-running script per node."""

    procs = {} # node_name -> (proc, log_path)
    node_names = test_cfg.node_names()
    tmpdir_path = test_cfg.tmpdir_path()
    kwargs = arion_subprocess_kwargs(test_cfg, arion_dir)
    for node_name in node_names:
        log_path = tmpdir_path / 'data' / node_name / 'egc' / 'test.log'
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
    results = {}
    for node_name, (p, log_handle) in procs.items():
        try:
            p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        finally:
            log_handle.close()
        results[node_name] = p.returncode
    error_codes = {k:v for k,v in results.items() if v != 0}
    assert len(error_codes) == 0, f'Script error codes: {error_codes}' # TODO plain assert for pytest?
    return results # TODO remove?


