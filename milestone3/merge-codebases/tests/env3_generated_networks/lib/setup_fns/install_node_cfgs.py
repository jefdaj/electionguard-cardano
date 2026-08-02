import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging
from typing import Optional
from ..config import ResolvedTestConfig

LOG = logging.getLogger(__name__)

# TODO actual type for this?
def _admin_config(cfg: ResolvedTestConfig) -> dict:
    acfg = {}
    acfg['ceremony'] = asdict(cfg.config.nodes.guardians)
    acfg['manifest'] = {} # TODO finish writing
    return acfg

def install_node_cfgs(cfg: ResolvedTestConfig):
    "Split the main test.json config into relevant fields per node."
    node_counts = {
        'admin':    1,
        'guardian': cfg.config.nodes.guardians.count,
        'device':   cfg.config.nodes.devices.count,
        'verifier': cfg.config.nodes.verifiers.count,
    }
    for (node_role, n_nodes) in node_counts.items():
        for node_index in range(1, n_nodes+1):
            node_name = 'admin' if node_role == 'admin' else f'{node_role}{node_index}'
            out_path = cfg.private_path(node_name) / 'egc' / 'config.json'
            if node_role == 'admin':
                ncfg = _admin_config(cfg)
                LOG.debug(f'write {out_path}')
                out_path.write_text( ncfg.to_json() )
