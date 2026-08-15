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

# TODO where should this live?
def _guard_election(state):
    try:
        election_cfg = state.node.election_cfg # TODO any better way?
    except:
        raise HTTPException(status_code=409, detail="Subscribe to an election first.")

@router.get("/await")
async def phase_await(
        params: Annotated[schemas.Phase, Query()],
        state=Depends(get_state)
    ):
    _guard_election(state)
    phase_ = EgcPhase(params.egc_phase_value)
    state.node.await_phase(phase=phase_)
    return Response(status_code=201)

# TODO where should this live?
def _guard_admin(state):
    try:
        assert state.node.channel_id() == ADMIN_CHANNEL_ID
    except:
        raise HTTPException(status_code=409, detail="Only the admin can do that.")

@router.put("", status_code=201)
async def phase_advance(
        data: schemas.Phase,
        state = Depends(get_state)
    ):
    LOG.debug('phase_advance')
    _guard_election(state)
    _guard_admin(state)

    # This one has to be translated back to the on-chain type first
    # TODO adjust the CLI to take an explicit on-chain phase name instead?
    egc_old = state.node.current_phase()    ; LOG.debug(f'egc_old: {egc_old}')
    egc_new = EgcPhase(data.egc_phase_value); LOG.debug(f'egc_new: {egc_new}')
    old = resolve_onchain_phase(egc_old)    ; LOG.debug(f'old: {old}')
    new = resolve_onchain_phase(egc_new)    ; LOG.debug(f'new: {new}')
    if new is None:
        raise HTTPException(
            status_code=409,
            detail=f"No on-chain phase matches {egc_phase}."
        )
    guard_phase_transition(old, new)

    LOG.debug('submitting tx.')
    tx = state.node.advance_phase(new_phase=new)
    LOG.debug('submitted tx. waiting to confirm')
    state.node.await_tx_confirmed(tx)
