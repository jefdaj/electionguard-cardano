import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging
from typing import Optional
from ..config import ResolvedTestConfig
from ....lib.json_utils import fancy_dumps

LOG = logging.getLogger(__name__)

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
            egc_dir = cfg.private_path(node_name) / 'egc'
            if node_role == 'admin':

                # write ceremony config
                out1 = egc_dir / 'ceremony.json'
                str1 = fancy_dumps(cfg.config.nodes.guardians)
                LOG.debug(f'str1: {str1}')
                LOG.debug(f'write {out1}')
                out1.write_text(str1)

                # TODO write manifest config

            # TODO write device configs
