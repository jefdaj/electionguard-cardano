from ....lib.json_utils import fancy_raw
from ..config import ResolvedTestConfig
import logging

LOG = logging.getLogger(__name__)

from .render_egc_scripts import render_egc_scripts
from .install_qrcode     import install_qr_txt, install_qr_png
from .install_funder_sk  import install_funder_sk
from .install_node_cfgs  import install_node_cfgs
from .install_n_subs     import install_n_subs

def run_setup_fns(cfg: ResolvedTestConfig):
    "Pull fn names + args from cfg and run them."
    for fn_call in cfg.config.pytest.setup_fns.fns:
        fn = globals()[fn_call.name]
        LOG.debug(f'run_setup_fns fn: {fn.__name__}')
        kwargs = fn_call.to_dict(lambda x:x)['args']
        LOG.debug(f'run_setup_fns kwargs: {kwargs}')
        try:
            fn(cfg=cfg, **kwargs)
        except Exception as e:
            LOG.error(e)
            raise
