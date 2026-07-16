import json
from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
import shutil
from egc import *

router = APIRouter(prefix="/wallet")

# For now we only need one wallet at a time, the same way we only need one
# election at a time. So put seems reasonable here.

def _wallet_path(state) -> Path:
    wallet_dir = state.config['node']['private_dir']
    sk_path = (wallet_dir / 'wallet').with_suffix('.sk')
    return sk_path

@router.put("")
async def wallet_load_or_create(wallet_dict: dict, state=Depends(get_state)):
    description = wallet_dict['description']
    sk_dict = wallet_dict['sk_dict']
    sk_path = _wallet_path(state)
    if sk_dict is None:
        # TODO capture verbose msg here and return to cli?
        state.wallet = create_wallet(
            keys_dir    = sk_path.absolute().parent,
            name        = 'wallet', # only one stored on the server at a time
            description = description,
            verbose     = True, # TODO False
            overwrite   = True,
        )
    else:
        state.wallet = Wallet.from_json(json.dumps(sk_dict))
        sk_path.absolute().parent.mkdir(parents=True, exist_ok=True)
        state.wallet.save(sk_path)
    return 201

@router.get("")
async def wallet_show(state=Depends(get_state)):
    if getattr(state, 'wallet', None) is None:
        return {} # TODO None?
    cfg = {
        'description': state.wallet.sk.description, # TODO to json first?
        'addr': str(state.wallet.addr),
        'vkh' : str(state.wallet.vkh),
    }
    return cfg

# TODO warning before deleting the wallet sk?
@router.delete("")
async def wallet_clear(state=Depends(get_state)):
    state.wallet = None
    sk_path = _wallet_path(state)
    shutil.rmtree(sk_path, ignore_errors=True)

# TODO _sk in the name? export?
@router.get("/save")
async def wallet_save(state=Depends(get_state)):
    return state.wallet.to_json()
