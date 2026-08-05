from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from egc_app import schemas

router = APIRouter(prefix="/records")

@router.get("")
async def records_list(state=Depends(get_state)):
    metas = state.node.batch_list() # should be sorted already
    data = schemas.RecordsListOut(records=metas)
    return data
