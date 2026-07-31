from fastapi import APIRouter, Depends, Request, Response
from fastapi import HTTPException
from dataclasses import asdict
from egc_app.server.state import get_state, reset_election_state
from egc import *
import asyncio
import json
from fastapi.responses import StreamingResponse
from egc_app import schemas
from starlette.status import HTTP_504_GATEWAY_TIMEOUT

import logging
LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/election", tags=["election"])


def _log_event(event: ChannelEvent) -> None:
    LOG.debug(f'election event:\n{event.to_raw()}')

def _log_error(err: ElectionError) -> None:
    LOG.error(f'election error:\n{err.to_raw()}')

def _subscribe_to_election_config(state, election_config: ElectionConfig):
    "Shared logic used by start_subscriber and create_election."
    reset_election_state(state)
    state.node.subscribe(
        election_config,
        on_event = _log_event,
        on_error = _log_error,
    )
    state.config['election'] = asdict(election_config)

@router.put("/subscribe")
def start_subscriber(data: schemas.ElectionSubscribe, state=Depends(get_state)):
    _subscribe_to_election_config(state, data.config)
    return Response(status_code=201)


def _context_backup_json_path(state):
    private_dir = state.config['node']['private_dir']
    backup_path = (private_dir / 'election-context').with_suffix('.json')
    return backup_path

@router.post("/create")
def create_election(data: schemas.ElectionCreate, state=Depends(get_state)):

    if state.wallet is None:
        # TODO create one automatically?
        raise HTTPException(status_code=409, detail="Load or create a wallet first.")

    # create temporary funder node
    funder_wallet = Wallet.from_signing_key(data.funder_sk)
    tmp_funder_node = FunderNode(wallet=funder_wallet)

    # create the election
    (tx, election_cfg) = tmp_funder_node.init_election(
        admin_vkh = data.admin_vkh,
        admin_ada = data.admin_ada,
        subscribe = False,
        context_backup_json = _context_backup_json_path(state),
    )

    # TODO wait to subscribe until after tx confirms?
    _subscribe_to_election_config(state, election_cfg)

    # TODO actually, could we skip the wait?
    try:
        state.node.wait_for_confirmation(tx) # TODO make this async?
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(
            status_code = HTTP_504_GATEWAY_TIMEOUT,
            default = f"TX failed to confirm: {tx}",
        )

    return Response(status_code=201)


@router.get("/burntesttokens")
def burn_test_tokens(state=Depends(get_state)):
    # The wait here is necessary because whoever burns the tokens needs to get
    # this TX confirmed before returning their collateral.
    burn_tx = state.node.burn_test_tokens()
    state.node.wait_for_confirmation(burn_tx)

@router.get("/events")
async def stream_events(request: Request, state=Depends(get_state)):
    if state.node is None:
        raise HTTPException(404)

    async def gen():
        sent = 0
        while True:
            if await request.is_disconnected():
                break
            events = state.node.subscriber.all_election_events() # full list, grows over time
            # The data: and : (comment line) thing is part of the SSE spec
            for event in events[sent:]:     # only the new tail
                yield f"data: {event.to_raw()}\n\n" # double newline dispatches SSE event
            sent = len(events)
            if len(events) == sent:      # nothing new
                yield ": keepalive\n\n"  # comment line, ignored by client
            await asyncio.sleep(OGMIOS_POLL_SEC)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
