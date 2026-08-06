from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from egc_app import schemas
import logging

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/records")

@router.get("")
async def records_list(state=Depends(get_state)):
    metas = state.node.batch_list() # already sorted
    LOG.debug(f'metas: {metas}')
    data = schemas.RecordsListOut(records=metas)
    LOG.debug(f'data: {data}')
    return data
