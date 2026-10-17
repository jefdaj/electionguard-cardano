from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/collateral")

@router.post("/return")
async def return_collateral(data: schemas.CollateralReturn, state=Depends(get_state)):
    state.node.return_collateral(return_addr=data.return_addr)

@router.get("/await")
async def collateral_await(state=Depends(get_state)):
    if state.wallet is None:
        raise HTTPException(status_code=409, detail="Load or create a wallet first.")
    try:
        state.node.await_collateral()
        return Response(status_code=204) # success, no content
    except (TimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Timed out waiting for collateral")
