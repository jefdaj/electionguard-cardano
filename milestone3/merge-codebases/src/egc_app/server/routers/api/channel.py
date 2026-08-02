import asyncio
from fastapi import APIRouter, Depends, HTTPException
from egc_app.server.state import get_state
from egc_app import schemas
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/channel")

# TODO sync rather than async?
@router.get("/await")
async def channel_await(data: schemas.ChannelAwait, state=Depends(get_state)):
    if state.wallet is None:
        raise HTTPException(status_code=409, detail="Load or create a wallet first.")
    try:
        ch_str = state.node.await_channel(data.role)
        return schemas.ChannelAwaitOut(ch_str)
    except (TimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, "Timed out waiting for channel")
