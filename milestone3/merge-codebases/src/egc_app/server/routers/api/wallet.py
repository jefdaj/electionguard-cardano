import json
from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
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
async def wallet_load_or_create(data: schemas.WalletLoadOrCreate, state=Depends(get_state)):
    sk_path = _wallet_path(state)
    if isinstance(data.sk_or_desc, SigningKey):
        # got sk; derive wallet
        state.wallet = Wallet.from_signing_key(data.sk_or_desc)
        state.wallet.save(sk_path)
    else:
        # got description; generate wallet
        assert isinstance(data.sk_or_desc, str)
        state.wallet = create_wallet(
            keys_dir    = sk_path.absolute().parent,
            name        = 'wallet', # only one stored on the server at a time
            description = data.sk_or_desc,
            verbose     = True, # TODO False
            overwrite   = True, # TODO 409 if no ?force=true or similar included too
        )
    state.node.publisher.wallet = state.wallet
    return Response(status_code=201)

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
