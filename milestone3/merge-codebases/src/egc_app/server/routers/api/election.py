from fastapi import APIRouter, Depends, Request
from fastapi import HTTPException
from dataclasses import asdict
from egc_app.server.state import get_state, reset_election_state
from egc import *
import asyncio
import json
from fastapi.responses import StreamingResponse

import logging

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/election", tags=["election"])

@router.put("/subscribe")
async def start_subscriber(config: ElectionConfig, state=Depends(get_state)):

    # Reset election-specific state, leaving alone the config, wallet, etc
    reset_election_state(state)

    state.config['election'] = asdict(config)

    state.node = ObserverNode(
        role_index = 1, # TODO pass this in
        wallet     = state.wallet,
    )

    def log_event(event: ChannelEvent) -> None:
        LOG.debug(f'election event:\n{event.to_raw()}')

    def log_error(err: ElectionError) -> None:
        LOG.error(f'election error:\n{err.to_raw()}')

    state.node.subscribe(
        config,
        on_event = log_event,
        on_error = log_error,
    )

    return 201

@router.get("/events") # TODO response model?
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
