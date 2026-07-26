from ....lib.json_utils import fancy_raw
from ..config import ResolvedTestConfig
import logging

LOG = logging.getLogger(__name__)

from .render_egc_scripts import render_egc_scripts
from .write_qrcode       import write_qr_str, write_qr_png

def run_setup_fns(cfg: ResolvedTestConfig):
    "Pull fn names + args from cfg and run them."
    for fn_call in cfg.config.pytest.setup_fns.fns:
        fn = globals()[fn_call.name]
        LOG.debug(f'run_setup_fns fn: {fn.__name__}')
        kwargs = fn_call.to_dict(lambda x:x)['args'] # TODO how should this be done?
        LOG.debug(f'run_setup_fns kwargs: {kwargs}')
        fn(cfg=cfg, **kwargs)
