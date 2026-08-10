import json
from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
import shutil
from egc import *

import logging
LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/ipfs") # TODO /ipfs_nodes?

def show_node(ipfs_node: IpfsNode) -> schemas.IpfsNodeOut:
    LOG.debug(f'show_node {ipfs_node}')
    return schemas.IpfsNodeOut(
        peer_id = ipfs_peerid_to_string(ipfs_node.peer_id),
        addr_hints = [
            ipfs_multiaddr_to_string(s)
            for s in ipfs_node.addr_hints
        ]
    )

@router.get("")
async def ipfs_show(state=Depends(get_state)):
    LOG.debug('ipfs_show')
    if getattr(state, 'node', None) is None:
        nodes = []
    else:
        nodes = {
            channel_id_to_string(ch_id) : show_node(n)
            for (ch_id, n) in state.node.ipfs.channel_nodes.items()
        }
    return schemas.IpfsNodesOut(channel_nodes = nodes)

@router.put("")
async def ipfs_post(state=Depends(get_state)):
    LOG.debug('ipfs_post')
    tx = state.node.set_ipfs_node()
    state.node.await_tx_confirmed(tx)
    return Response(status_code=201)
