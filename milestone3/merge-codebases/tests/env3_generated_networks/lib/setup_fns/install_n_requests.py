import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Optional
from ..config import ResolvedTestConfig
from ....lib.json_utils import fancy_dumps, fancy_raw

import logging
LOG = logging.getLogger(__name__)

def install_n_requests(cfg: ResolvedTestConfig):
    "Tell the admin how many subchannel requests to expect."
    LOG.debug('install_n_requests')
    node_counts = {
        # 'admin': 1,
        'guardian': cfg.config.nodes.guardians.number_of_guardians,
        'device':   cfg.config.nodes.devices.count,
        'verifier': cfg.config.nodes.verifiers.count,
    }
    n_expected = sum(node_counts.values())
    LOG.debug(f'install_n_n=requests n_expected: {n_expected}')
    out = cfg.private_path('admin') / 'egc' / 'n_requests.txt'
    egc_dir = out.parent
    LOG.debug(f'install_n_requests mkdir {egc_dir}')
    egc_dir.mkdir(parents=True, exist_ok=True)
    LOG.debug(f'install_n_requests write {out}')
    out.write_text(str(n_expected))
