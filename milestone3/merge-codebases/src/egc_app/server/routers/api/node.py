import json
from fastapi import APIRouter, Depends
from egc.core.ogmios import ogmios_health, ogmios_wait_until_synced
from egc_app.schemas.node import NodeStatusOut

router = APIRouter(prefix="/node", tags=["status"])

# TODO GET /node -> ?

# TODO is /health more standard?
@router.get("/status") # , response_model=NodeStatusOut)
async def status(state=Depends(get_state)):
    try:
        cstat = await ogmios_health()
        cstat2 = {}
        cstat2['connected'] = cstat['connectionStatus'] == 'connected'
        cstat2['sync_percent'] = int(cstat['networkSynchronization'] * 100)
    # print(f'cstat2: {cstat2}')
    except:
        cstat2 = {'connected': False} # TODO codify better
    try:
        istat = await state.node.ipfs.ipfs_status()
        istat['connected'] = True
    except:
        istat = {'connected': False}
    return json.dumps({'cardano': cstat2, 'ipfs': istat})

@router.get("/await")
async def await_(state=Depends(get_state)):
    await state.node.ipfs.wait_until_stable()
    await ogmios_wait_until_synced()
    return
