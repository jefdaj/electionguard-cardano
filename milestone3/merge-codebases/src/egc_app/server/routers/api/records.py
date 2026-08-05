from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
from copy import deepcopy
from dataclasses import asdict

router = APIRouter(prefix="/records")

@router.get("")
async def records_list(state=Depends(get_state)):
    raise NotImplementedError
