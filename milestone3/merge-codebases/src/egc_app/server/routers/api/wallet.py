import json
from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from egc import *

router = APIRouter(prefix="/wallet")

# For now we only need one wallet at a time, the same way we only need one
# election at a time. So put seems reasonable here. We should be careful not to
# clobber existing wallet files though.

@router.put("")
async def wallet_load_or_create(wallet_dict: dict, state=Depends(get_state)):
    name = wallet_dict['name']
    keys_dir = state.config['private_dir'] / 'keys'
    sk_path = (keys_dir / name).with_suffix('.sk')
    if sk_path.exists():
        raise Exception(f'sk_path exists: {sk_path}') # TODO better error
    sk_dict = wallet_dict['sk_dict']
    if sk_dict is None:
        # TODO capture verbose msg here and return to cli?
        state.wallet = create_wallet(keys_dir=keys_dir, name=name, verbose=False)
    else:
        state.wallet = Wallet.from_json(json.dumps(sk_dict))
        state.wallet.save(sk_path)
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

# TODO should this delete the .sk file too?
@router.delete("")
async def wallet_clear(state=Depends(get_state)):
    state.wallet = None
    state.config['wallet_name'] = None

# TODO _sk in the name? export?
@router.get("/save")
async def wallet_save(state=Depends(get_state)):
    return state.wallet.to_json()
