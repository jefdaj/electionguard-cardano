from fastapi import APIRouter
from egc_app.server.schemas.status import StatusOut

router = APIRouter(tags=["status"])

@router.get("/status", response_model=StatusOut)
async def health():
    return StatusOut()
