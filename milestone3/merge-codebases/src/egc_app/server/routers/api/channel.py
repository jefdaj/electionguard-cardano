import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated
from egc_app.server.state import get_state
from egc_app import schemas
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/channel")

# TODO sync rather than async?
@router.get("/await")
async def channel_await(params: Annotated[schemas.ChannelAwait, Query()], state=Depends(get_state)):
    if state.wallet is None:
        raise HTTPException(status_code=409, detail="Load or create a wallet first.")
    try:
        ch_str = state.node.await_channel(params.role)
        return schemas.ChannelAwaitOut(channel_str=ch_str)
    except (TimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Timed out waiting for channel")
