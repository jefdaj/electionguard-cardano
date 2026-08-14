from fastapi import APIRouter, Depends, HTTPException, Query, Response
from egc_app.server.state import get_state
from copy import deepcopy
from dataclasses import asdict
from typing import Annotated
from egc_app import schemas
from egc import *
import logging


LOG = logging.getLogger(__name__)


router = APIRouter(prefix="/phase")


@router.get("")
async def phase_get(state=Depends(get_state)):
    phase_ =  state.node.current_phase()
    LOG.debug(f'phase_: {phase_}')
    out = schemas.Phase(egc_phase_value=phase_.value)
    return out

@router.get("/await")
async def phase_await(
        params: Annotated[schemas.Phase, Query()],
        state=Depends(get_state)
    ):
    # TODO better precondition(s)
    try:
        election_cfg = state.node.election_cfg # TODO _guard_election or similar instead?
    except:
        raise HTTPException(status_code=409, detail="Subscribe to an election first.")
    phase_ = EgcPhase(params.egc_phase_value)
    state.node.await_phase(phase=phase_)
    return Response(status_code=201)

@router.post("")
async def phase_advance(
        data: schemas.Phase,
        state = Depends(get_state)
    ):
    raise NotImplementedError
