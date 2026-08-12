import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated
from egc_app.server.state import get_state
from egc_app import schemas
from copy import deepcopy
from dataclasses import asdict
import re
import logging
from egc import *

# TODO is there any good way to make the node auto-swap without calling channel await explicitly?

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/channel")

CHANNEL_TYPES = {
    'admin':    AdminNode,
    'guardian': GuardianNode,
    'device':   DeviceNode,
    'verifier': VerifierNode,
}

# TODO sync rather than async?
@router.get("/await")
async def channel_await(params: Annotated[schemas.ChannelAwait, Query()], state=Depends(get_state)):
    if state.wallet is None:
        raise HTTPException(status_code=409, detail="Load or create a wallet first.")
    try:
        ch_str = state.node.await_channel(params.role) # TODO get index here rather than str?
        LOG.info(f'Authorized by admin to post on {ch_str} channel.')

        actual_role = re.sub(r"\d+$", "", ch_str)
        assert actual_role == params.role, f'role mismatch: expected {params.role}, got {actual_role}'

        # LOG.debug(f'node: {state.node.__dict__}')

        # swap for a new node type
        # TODO factor out into a util fn?
        old_cls = type(state.node)
        new_cls = CHANNEL_TYPES[actual_role]
        LOG.info(f'new_cls: {new_cls}')

        if new_cls == old_cls:
            LOG.info(f'Node is already an {new_cls.__name__}. No need to swap it out for the new role.')
        else:
            LOG.info(f'Node is an {old_cls.__name__}. Need to swap it out for an {new_cls.__name__}.')

            kwargs = {}
            # private_dir = state.node.private_dir,
            private_dir = state.config['node']['private_dir']
            # if isinstance(private_dir, tuple): # TODO why is it a tuple?
            #     private_dir = private_dir[0]
            kwargs['private_dir'] = private_dir
            if actual_role != 'admin':
                index = int(re.sub(r"^[a-z]*", "", ch_str))
                kwargs['role_index'] = index
            kwargs['wallet'] = state.wallet
            kwargs['election_cfg'] = state.node.election_cfg
            LOG.info(f'kwargs: {kwargs}')

            LOG.info(f'Swapping out node: {old_cls} -> {new_cls}.')
            state.node = new_cls(**kwargs)

        return schemas.ChannelAwaitOut(channel_str=ch_str)

    except (TimeoutError, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Timed out waiting for channel")

@router.get("/request")
async def channel_request(
        params: Annotated[schemas.ChannelRequest, Query()],
        state=Depends(get_state)
    ):
    if state.wallet is None:
        raise HTTPException(status_code=409, detail="Load or create a wallet first.")
    try:
        election_cfg = state.node.election_cfg
    except:
        raise HTTPException(status_code=409, detail="Subscribe to an election first.")
    data = schemas.ChannelRequestOut(
        requested_role         = params.requested_role,
        election_oneshot_hex   = election_cfg.oneshot_hex,
        election_network_magic = str(election_cfg.network_magic),
        publisher_vkh          = state.wallet.vkh,
    )
    LOG.debug(f'data: {data}')
    return data

@router.post("/create")
async def channel_create(
        data: schemas.ChannelRequestOut,
        state = Depends(get_state)
    ):
    try:
        election_cfg = state.node.election_cfg
    except:
        raise HTTPException(status_code=409, detail="Subscribe to an election first.")
    if election_cfg.oneshot_hex != data.election_oneshot_hex:
        raise HTTPException(status_code=409, detail="Request is for the wrong election.")
    if election_cfg.network_magic != data.election_network_magic:
        raise HTTPException(status_code=409, detail="Request is for the wrong Cardano network.")
    current_publishers = state.node.all_channel_publishers()
    if data.publisher_vkh in current_publishers:
        prev_role = current_publishers[vkh]
        raise HTTPException(
            status_code = 409,
            detail = f"Publisher {data.publisher_vkh} is already {prev_role}."
        )
