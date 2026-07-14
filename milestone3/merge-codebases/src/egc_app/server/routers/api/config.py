from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from copy import deepcopy

router = APIRouter(prefix="/config")

@router.get("")
async def config(state=Depends(get_state)):
    cfg = deepcopy(state.config)
    # TODO move wallet_name into wallet?
    cfg['wallet'] = {
        'addr': str(state.wallet.addr),
        'vkh' : str(state.wallet.vkh),
    }
    return cfg
