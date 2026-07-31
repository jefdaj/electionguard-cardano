import json
from fastapi import APIRouter
from egc.core.ogmios import ogmios_health, ogmios_wait_until_synced
from egc.core.ipfs import ipfs_wait_until_stable, ipfs_status
from egc_app.schemas.node import NodeStatusOut

router = APIRouter(prefix="/node", tags=["status"])

# TODO GET /node -> ?

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
    return json.dumps({'cardano': cstat2, 'ipfs': istat})

@router.get("/await")
async def await_():
    await ipfs_wait_until_stable()
    await ogmios_wait_until_synced()
    return
