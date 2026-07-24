import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .test_config import ResolvedTestConfig
# from .test_tmpdir import lock_test_tmpdir

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
                debug = True, # only a personal convention
            )
            log(f'write_egc_scripts write {out_path}')
            out_path.write_text(out_text)
            os.chmod(out_path, 0o755)

        log('write_egc_scripts done')

    return tmpdir_path
