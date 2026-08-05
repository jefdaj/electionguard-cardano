from fastapi import APIRouter, Depends
from egc_app.server.state import get_state
from egc_app import schemas

router = APIRouter(prefix="/records")

@router.get("")
async def records_list(state=Depends(get_state)):
    paths = state.node.batch_list()
    paths = [str(p) for p in paths]
    data = schemas.RecordsListOut(records=paths)
    return data
