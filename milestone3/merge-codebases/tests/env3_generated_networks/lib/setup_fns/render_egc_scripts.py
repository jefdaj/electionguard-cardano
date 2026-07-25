import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .config import ResolvedTestConfig
import logging

LOG = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / 'egc_script_templates'

JINJA_ENV = Environment(
    loader = FileSystemLoader(TEMPLATES_DIR),
    trim_blocks = True,
    lstrip_blocks = True,
    keep_trailing_newline = False,
)

def render_egc_scripts(
        cfg: ResolvedTestConfig,
        default:   Optional[str] = 'base.sh',
        admin:     Optional[str] = None,
        guardians: Optional[str] = None,
        devices:   Optional[str] = None,
        verifiers: Optional[str] = None,
    ):
    "Render egc scripts from their jinja2 templates."

    template_names = {
        'admin':    admin    if admin    else default,
        'guardian': guardian if guardian else default,
        'device':   device   if device   else default,
        'verifier': verifier if verifier else default,
    }

    node_counts = {
        'admin':    1,
        'guardian': cfg.nodes.guardians.count,
        'device':   cfg.nodes.devices.count,
        'verifier': cfg.nodes.verifiers.count,
    }

    tmpdir_path  = cfg.tmpdir_path()
    log_path     = cfg.log_path()
    scripts_path = tmpdir_path / 'egc_scripts'

    with log_path.open('a') as log_handle:
        # TODO rewrite with LOG
        def log(msg):
            log_handle.writelines([msg + '\n'])
            log_handle.flush()
        log('render_egc_scripts start')

        log(f'render_egc_scripts mkdir {scripts_path}')
        scripts_path.mkdir(parents=True, exist_ok=True)

        # for (node_role, node_cfg) in cfg.nodes.items():
        for (node_role, n_nodes) in node_counts:
            template_name = template_names[node_role]
            template = JINJA_ENV.get_template(template_name)
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
                log(f'render_egc_scripts write {out_path}')
                out_path.write_text(out_text)
                os.chmod(out_path, 0o755)

        log('render_egc_scripts done')
