from fastapi import APIRouter
from egc.core.ipfs import ipfs_wait_until_stable
from egc_app.server.schemas.node import StatusOut

router = APIRouter(tags=["status"])

# TODO include ogmios status here
# TODO include ipfs status here
@router.get("/status", response_model=StatusOut)
async def status():
    return StatusOut()

@router.get("/await")
async def await_():
    await ipfs_wait_until_stable()
    # TODO also wait for ogmios sync progress == 1.0 here
    return 200 # TODO is this right?
