from fastapi import APIRouter
from egc.core.ogmios import ogmios_health
from egc.core.ipfs import ipfs_wait_until_stable, ipfs_status
from egc_app.server.schemas.node import NodeStatusOut

router = APIRouter(prefix="/node", tags=["status"])

# TODO is /health more standard?
@router.get("/status") # , response_model=NodeStatusOut)
async def status():
    try:
        cstat = await ogmios_health()
        cstat2 = {}
        cstat2['connected'] = cstat['connectionStatus'] == 'connected'
        cstat2['sync_percent'] = int(cstat['networkSynchronization'] * 100)
    # print(f'cstat2: {cstat2}')
    except:
        cstat2 = {'connected': False} # TODO codify better
    try:
        istat = await ipfs_status()
        istat['connected'] = True
    except:
        istat = {'connected': False}
    return {'cardano': cstat2, 'ipfs': istat}

@router.get("/await")
async def await_():
    # TODO wait for ogmios sync progress == 1.0 here
    await ipfs_wait_until_stable()
    return
