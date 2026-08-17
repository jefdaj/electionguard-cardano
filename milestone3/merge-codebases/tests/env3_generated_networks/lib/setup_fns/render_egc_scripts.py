import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging
from typing import Optional
from ..config import ResolvedTestConfig

LOG = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / 'egc_script_templates'

JINJA_ENV = Environment(
    loader = FileSystemLoader(TEMPLATES_DIR),
    trim_blocks = True,
    lstrip_blocks = True,
    keep_trailing_newline = False,

    # change bracket -> square bracket comment delimiters,
    # because brackets can be used in bash arrays
    # TODO also change the rest to match?
    # block_start_string='[%',
    # block_end_string='%]',
    # variable_start_string='[[',
    # variable_end_string=']]',
    comment_start_string='[#',
    comment_end_string='#]',
)

def render_egc_scripts(
        cfg: ResolvedTestConfig,
        default:  Optional[str] = 'base.sh',
        admin:    Optional[str] = None,
        guardian: Optional[str] = None,
        device:   Optional[str] = None,
        verifier: Optional[str] = None,
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
        'guardian': cfg.config.nodes.guardians.number_of_guardians,
        'device':   cfg.config.nodes.devices.count,
        'verifier': cfg.config.nodes.verifiers.count,
    }

    tmpdir_path  = cfg.tmpdir_path()
    log_path     = cfg.log_path()
    scripts_path = tmpdir_path / 'egc_scripts'

    # with log_path.open('a') as log_handle:
        # TODO rewrite with LOG
        # def log(msg):
        #     log_handle.writelines([msg + '\n'])
        #     log_handle.flush()
    LOG.debug('render_egc_scripts start')

    LOG.debug(f'render_egc_scripts mkdir {scripts_path}')
    scripts_path.mkdir(parents=True, exist_ok=True)

    # for (node_role, node_cfg) in cfg.nodes.items():
    for (node_role, n_nodes) in node_counts.items():
        template_name = template_names[node_role]
        LOG.debug(f'template_name: {template_name}')
        try:
            template = JINJA_ENV.get_template(template_name)
        except Exception as e:
            LOG.error(f'Error while loading template {template_name}: {e}')
            raise
        LOG.debug('loaded template')
        for node_index in range(1, n_nodes+1):
            node_name = 'admin' if node_role == 'admin' else f'{node_role}{node_index}'
            out_path = scripts_path / f'{node_name}.sh'
            LOG.debug(f'out_path: {out_path}')
            out_text = template.render(
                node_name    = node_name,
                node_role    = node_role,
                node_index   = node_index,
                # template_name = template_name,
                debug_script = True,
            )
            LOG.debug(f'render_egc_scripts write {out_path}')
            out_path.write_text(out_text)
            os.chmod(out_path, 0o755)

    LOG.debug('render_egc_scripts done')
