from fastapi import APIRouter, Depends, Request
from fastapi import HTTPException
from dataclasses import asdict
from egc_app.server.state import get_state, reset_election_state
from egc import *
import asyncio
import json
from fastapi.responses import StreamingResponse

from .subscription import router as subscription_router
from .actions.router import router as actions_router

import logging

LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/election", tags=["election"])
router.include_router(subscription_router)
router.include_router(actions_router)

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
