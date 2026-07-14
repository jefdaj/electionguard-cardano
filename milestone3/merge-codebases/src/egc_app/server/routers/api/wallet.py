from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from egc import *

router = APIRouter(prefix="/wallet")

# For now we only need one wallet at a time, the same way we only need one
# election at a time. So put seems reasonable here. We should be careful not to
# clobber existing wallet files though.

@router.put("")
async def wallet_create(wallet_dict: dict, state=Depends(get_state)):
    name = wallet_dict['name']
    keys_dir = state.config['private_dir'] / 'keys'
    # TODO capture verbose msg here and return to cli?
    state.wallet = create_wallet(keys_dir=keys_dir, name=name, verbose=False)
    state.config['wallet_name'] = name
    return 201

@router.get("")
async def wallet_show(state=Depends(get_state)):
    cfg = {
        'name': state.config['wallet_name'],
        'addr': str(state.wallet.addr),
        'vkh' : str(state.wallet.vkh),
    }
    return cfg

@router.post("/clear")
async def wallet_clear(state=Depends(get_state)):
    state.wallet = None
    state.config['wallet_name'] = None
