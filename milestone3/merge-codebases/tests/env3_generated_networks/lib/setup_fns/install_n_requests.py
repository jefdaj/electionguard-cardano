import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging
from typing import Optional
from ..config import ResolvedTestConfig
from ....lib.json_utils import fancy_dumps, fancy_raw

LOG = logging.getLogger(__name__)

def install_n_requests(cfg: ResolvedTestConfig):
    "Tell the admin how many subchannel requests to expect."
    node_counts = {
        # 'admin': 1,
        'guardian': cfg.config.nodes.guardians.number_of_guardians,
        'device':   cfg.config.nodes.devices.count,
        'verifier': cfg.config.nodes.verifiers.count,
    }
    n_expected = sum(node_counts.values())
    LOG.debug(f'n_expected: {n_expected}')
    out = cfg.private_path('admin') / 'egc' / 'n_requests.txt'
    out.write(str(n_expected))
    LOG.debug(f'wrote {out}')
