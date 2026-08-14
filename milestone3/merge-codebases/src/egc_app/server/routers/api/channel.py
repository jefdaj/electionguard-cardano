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

import logging
LOG = logging.getLogger(__name__)

# TODO is there any good way to make the node auto-swap without calling channel await explicitly?

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/channel")

CHANNEL_TYPES = {
    'admin':    AdminNode,
    'guardian': GuardianNode,
    'device':   DeviceNode,
    'verifier': VerifierNode,
}


# TODO where should this live?
def channel_role_and_index(channel_id: ChannelId) -> tuple[str, int]:
    if channel_id == ADMIN_CHANNEL_ID:
        return ('admin', 1)
    ch_str = channel_id_to_string(channel_id)
    role  =     re.sub(r"[0-9]*$", "", ch_str)
    index = int(re.sub(r"^[a-z]*", "", ch_str))
    return (role, index)


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
            # TODO rewrite using channel_role_and_index
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


# TODO where should this live?
def pick_new_channel_ids(
        roles_by_vkh: dict[VerificationKeyHash, str],
        cur_ids: list[ChannelId],
    ) -> dict[VerificationKeyHash, str]:
    # TODO should this just assume the current ids are in order (none missing)?
    cur_ri_pairs = [
        channel_role_and_index(ch_id)
        for ch_id in cur_ids
    ]
    LOG.debug(f'cur_ri_pairs: {cur_ri_pairs}')
    # cur_indexes = {
    #     'guardian': [],
    #     'device':   [],
    #     'verifier': [],
    # }
    # for (role, index) in cur_ri_pairs:
    #     cur_indexes[role].append(index)
    # LOG.debug(f'cur_indexes: {cur_indexes}')
    new_ri_pairs_by_vkh = {} # TODO no need for this intermediate format?
    for (vkh, role) in roles_by_vkh.items():
        # Note we *haven't* sorted this anywhere,
        # which makes it simple to match up all the test requests in order.
        # TODO is this a problem to rely on in the tests?
        LOG.debug(f'(vkh, role): {(vkh, role)}')
        i = 1
        # while i in cur_indexes[role]:
        while (role, i) in cur_ri_pairs or \
              (role, i) in new_ri_pairs_by_vkh.values():
            i += 1
        new_ri_pairs_by_vkh[vkh] = (role, i)
        # cur_indexes[role].append(i)
    LOG.debug(f'new_ri_pairs_by_vkh: {new_ri_pairs_by_vkh}')
    vkhs_by_ch_id = {
        coerce_channel_id(f'{r}{i}'): v
        for (v, (r, i)) in new_ri_pairs_by_vkh.items()
    }
    LOG.debug(f'vkhs_by_ch_id: {vkhs_by_ch_id}')
    return vkhs_by_ch_id


@router.post("/create")
async def channel_create(
        # reqs: list[schemas.ChannelRequestOut],
        data: schemas.ChannelCreate,
        state = Depends(get_state)
    ):
    LOG.debug(f'data: {data}')

    try:
        election_cfg = state.node.election_cfg
    except:
        raise HTTPException(status_code=409, detail="Subscribe to an election first.")

#     try:
#         # TODO use node class instead?
#         LOG.info(f'node cls: {type(self.node)}')
#         LOG.info(f'channel_id: {self.node.channel_id()}')
#         # assert self.node.channel_id() == ADMIN_CHANNEL_ID
#     except:
#         raise HTTPException(status_code=409, detail="Only the admin can add subchannels.")

    vkhs_set = set()
    for req in data.requests:
        vkh = req.publisher_vkh
        if vkh in vkhs_set:
            raise HTTPException(status_code=409, detail=f"Duplicate request for {vkh}.")
        else:
            vkhs_set.add(vkh)

    for req in data.requests:
        if election_cfg.oneshot_hex != req.election_oneshot_hex:
            raise HTTPException(status_code=409, detail="Request is for the wrong election.")
        if election_cfg.network_magic != req.election_network_magic:
            raise HTTPException(status_code=409, detail="Request is for the wrong Cardano network.")
        current_publishers = state.node.all_channel_publishers()
        if req.publisher_vkh in current_publishers:
            prev_role = current_publishers[vkh]
            raise HTTPException(
                status_code = 409,
                detail = f"Publisher {req.publisher_vkh} is already {prev_role}."
            )

    roles_by_vkh = {
        r.publisher_vkh: r.requested_role
        for r in data.requests
    }
    LOG.debug(f'roles_by_vkh: {roles_by_vkh}')
    cur_ids = state.node.subscriber.all_channel_ids()
    LOG.debug(f'cur_ids: {cur_ids}')
    vkhs_by_ch_id = pick_new_channel_ids(roles_by_vkh, cur_ids)
    LOG.debug(f'vkhs_by_ch_id: {vkhs_by_ch_id}')
    state.node.add_subchannels(
        subchannels     = vkhs_by_ch_id,
        subchannel_ada  = data.ada_per_channel,
        done_onboarding = data.done_onboarding,
    )
