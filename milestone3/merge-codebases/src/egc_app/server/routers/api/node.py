from fastapi import APIRouter
from egc.core.ipfs import ipfs_wait_until_stable, ipfs_status
from egc_app.server.schemas.node import NodeStatusOut

router = APIRouter(prefix="/node", tags=["status"])

@router.get("/status", response_model=NodeStatusOut)
async def status():
    # TODO status1 is cardano
    status2 = await ipfs_status()
    print(f'status2: {status2}')
    return NodeStatusOut(
        ipfs_peers = status2['peers'],
        ipfs_bw_bs = int(status2['rate']),
    )

@router.get("/await")
async def await_():
    # TODO wait for ogmios sync progress == 1.0 here
    await ipfs_wait_until_stable()
    return 200 # TODO is this right?
