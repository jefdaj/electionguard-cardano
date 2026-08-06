from fastapi import APIRouter, Depends, HTTPException
from egc_app.server.state import get_state
from egc_app import schemas
import logging
import shutil

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
    tx = state.node.post_public_records(
        new_record_pairs = pairs,
        new_phase = None, # TODO parse str -> ElectionPhase and add here
    )
    state.node.await_tx_confirmed(tx)
