from fastapi import APIRouter, Depends
from egc_app.server.deps import get_state
from egc_app.server.schemas.trivial import TrivialOut

router = APIRouter(tags=["trivial"])

@router.get("/trivial", response_model=TrivialOut)
async def get_trivial_route(state=Depends(get_state)):
    return TrivialOut(n=state.trivial)

@router.put("/trivial/{n}", response_model=TrivialOut)
async def set_state_route(n: int, state=Depends(get_state)):
    state.trivial = n
    return TrivialOut(n=n)
