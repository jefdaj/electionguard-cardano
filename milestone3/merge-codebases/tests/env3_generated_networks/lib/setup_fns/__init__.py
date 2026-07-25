from ..lib.json_utils import fancy_raw
from .test_config import ResolvedTestConfig
from .render_egc_scripts import render_egc_scripts
import logging

LOG = logging.getLogger(__name__)

def run_setup_fns(cfg: ResolvedTestConfig):
    "Pull fn names + args from cfg and run them."
    for fn_call in cfg.pytest.setup_fns.fns:
        fn = globals()[fn_call.name]
        LOG.debug(f'run_setup_fns fn: {fn.__name__}'
        kwargs = fancy_raw(fn_call.args) # TODO is this right?
        LOG.debug(f'run_setup_fns kwargs: {kwargs}'
        fn(cfg=cfg, **kwargs)
