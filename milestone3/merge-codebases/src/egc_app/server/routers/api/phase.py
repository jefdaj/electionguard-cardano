from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/phase")

@router.get("")
async def phase_get(state=Depends(get_state)):
    phase =  state.node.current_phase()
    print(f'phase: {phase}')
    return phase
