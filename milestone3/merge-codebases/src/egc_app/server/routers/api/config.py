from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/config")

@router.get("")
async def config(state=Depends(get_state)):
    cfg = deepcopy(state.config)

    # TODO how much of the wallet should actually go in the config?
    # TODO to match CLI args, just the name right?
    name = cfg.pop('wallet_name')
    if state.wallet is not None:
        wallet_cfg = {
            'addr': str(state.wallet.addr),
            'vkh': str(state.wallet.vkh),
        }
        if name:
            wallet_cfg['name'] = name
        cfg['wallet'] = wallet_cfg

    try:
        cfg['election'] = state.node.subscriber.config
    except AttributeError:
        pass
    return cfg
