from fastapi import APIRouter, Depends
from egc_app.server.state import get_state

router = APIRouter(prefix="/config")

@router.get("")
async def config(state=Depends(get_state)):
    return state.config
