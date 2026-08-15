from fastapi import APIRouter, Depends, HTTPException, Query
from egc_app.server.state import get_state
from egc_app import schemas
from typing import Annotated
import logging
import shutil
import time

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/records")

@router.get("")
async def records_list(state=Depends(get_state)):
    metas = state.node.batch_list() # already sorted
    LOG.debug(f'metas: {metas}')
    data = schemas.RecordsListOut(records=metas)
    LOG.debug(f'data: {data}')
    return data

@router.delete("")
async def records_drop(data: schemas.RecordsDrop, state=Depends(get_state)):
    # reverse so affected indexes don't change during delete
    idxs = sorted(data.indexes_to_drop, reverse=True)
    idxs = [i-1 for i in idxs] # make zero indexed
    paths = state.node.batch_list_paths() # already sorted
    if idxs and (idxs[0] >= len(paths) or idxs[-1] < 0):
        raise HTTPException(400, "Index out of range")
    for i in idxs:
        path = paths[i]
        LOG.info(f'delete record {i+1}: {path}') # display as 1-indexed
        path.unlink(missing_ok=False)

@router.post("/post", status_code=201)
def records_post(data: schemas.RecordsPost, state=Depends(get_state)):
    pairs = state.node.batch_assemble(
        indexes = data.indexes_to_post,
        min_size = data.min_size,
        max_size = data.max_size,
    )
    LOG.info(f'pairs: {pairs}')

    if data.new_phase:
        # TODO factor this out? it's partially duplicated in phase_advance
        egc_old = state.node.current_phase(); LOG.debug(f'egc_old: {egc_old}')
        egc_new = EgcPhase(data.new_phase)  ; LOG.debug(f'egc_new: {egc_new}')
        old = resolve_onchain_phase(egc_old); LOG.debug(f'old: {old}')
        new = resolve_onchain_phase(egc_new); LOG.debug(f'new: {new}')
        if new is None:
            raise HTTPException(
                status_code=409,
                detail=f"No on-chain phase matches {egc_phase}."
            )
        guard_phase_transition(old, new)
    else:
        new = None

    tx = state.node.post_public_records(
        new_record_pairs = pairs,
        new_phase = new,
    )
    state.node.await_tx_confirmed(tx)

@router.get("/await", status_code=200)
async def records_await(params: Annotated[schemas.RecordsAwait, Query()], state=Depends(get_state)):
    state.node.await_records(timeout=params.timeout)
    # TODO do I have to return anything?
