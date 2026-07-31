from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/collateral")

@router.post("/return")
async def return_collateral(state=Depends(get_state)):
    state.node.return_collateral()
