import json
from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
import shutil
from egc import *

import logging
LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/ipfs") # TODO /ipfs_nodes?

def node_out(opt_node: OptionIpfsNode) -> Optional[schemas.IpfsNodeOut]:
    LOG.debug(f'opt_node: {opt_node}')
    if isinstance(opt_node, NoIpfsNode):
        return None
    assert isinstance(opt_node, SomeIpfsNode), f'unexpected opt_node: {opt_node}'
    node = opt_node.value
    return schemas.IpfsNodeOut(
        peer_id = ipfs_peerid_to_string(node.peer_id),
        addr_hints = [
            ipfs_multiaddr_to_string(s)
            for s in node.addr_hints
        ]
    )

@router.get("")
async def ipfs_show(state=Depends(get_state)):
    LOG.debug('ipfs_show')
    # TODO raise error if can't get own id
    # if getattr(state, 'node', None) is None:
    #     ch_nodes = []
    # else:
    own_node = state.node.ipfs.get_own_node()
    LOG.debug(f'own_node: {own_node}')
    ch_nodes = {
        channel_id_to_string(ch_id) : node_out(n)
        for (ch_id, n) in state.node.ipfs.channel_nodes.items()
        if node_out(n) is not None
    }
    LOG.debug(f'ch_nodes: {ch_nodes}')
    data = schemas.IpfsNodesOut(
        own_node      = node_out(own_node),
        channel_nodes = ch_nodes,
    )
    LOG.debug(f'data: {data}')
    return data

@router.put("")
async def ipfs_post(state=Depends(get_state)):
    LOG.debug('ipfs_post')
    tx = state.node.set_ipfs_node()
    state.node.await_tx_confirmed(tx)
    return Response(status_code=201)
