from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/channel")

@router.get("/await")
async def channel_await(state=Depends(get_state)):
    raise NotImplementedError
    # TODO get own vkh or error 409
    # TODO with a timeout,
    # TODO poll for all channels
    # TODO filter by role
    # TODO if any has our key, return role_index
