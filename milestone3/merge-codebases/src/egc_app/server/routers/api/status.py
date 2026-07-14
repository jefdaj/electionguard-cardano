from fastapi import APIRouter
from egc_app.server.schemas.status import StatusOut

router = APIRouter(tags=["status"])

# TODO include ogmios status here
# TODO include ipfs status here
@router.get("/status", response_model=StatusOut)
async def health():
    return StatusOut()
