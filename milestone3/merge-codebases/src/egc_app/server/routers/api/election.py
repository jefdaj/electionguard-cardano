from fastapi import APIRouter, Depends, Request
from fastapi import HTTPException
from dataclasses import asdict
from egc_app.server.state import get_state, reset_election_state
from egc import *
import asyncio
import json
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/election", tags=["election"])

# TODO anything more needed to make clear POST election -> start_subscriber?
@router.put("")
async def start_subscriber(config: ElectionConfig, state=Depends(get_state)):

    # TODO proper auto-decode here
    # policy_id = ScriptHash(bytes.fromhex(config_dict['policy_id']))
    # config = ElectionConfig(
    #     policy_id   = policy_id,
    #     since_slot  = config_dict['since_slot'],
    #     since_block = config_dict['since_block'],
    # )
    # config = ElectionConfig.from_qrcode_str(qrcode_str)

    # Reset election-specific state, leaving alone the config, wallet, etc
    reset_election_state(state)

    # TODO defaultdict or something to avoid this?
    # state.config['election'] = {}
    state.config['election'] = asdict(config)

    # TODO integrate on_event with fastapi logging
    # state.subscriber = ElectionSubscriber(config, on_event=lambda e: None)
    # state.subscriber.start()
    state.node = ObserverNode(
        role_index = 1, # TODO pass this in
        wallet     = state.wallet,
    )
    state.node.subscribe(config)

    return 201

@router.get("/events") # TODO response model?
async def stream_events(request: Request, state=Depends(get_state)):

    if state.node is None:
        raise HTTPException(404)

    # config = state.subscriber.config
    # script_hash = ScriptHash(bytes.fromhex(policy_id))
    # if not script_hash == config.policy_id:
    #     raise HTTPException(409) # TODO proper idiom?

    async def gen():
        sent = 0
        while True:
            if await request.is_disconnected():
                break
            events = state.node.subscriber.all_election_events() # full list, grows over time
            # The data: and : (comment line) thing here is part of the SSE spec
            for event in events[sent:]:     # only the new tail
                yield f"data: {event.to_raw()}\n\n" # double newline dispatches SSE event
            sent = len(events)
            if len(events) == sent:      # nothing new
                yield ": keepalive\n\n"  # comment line, ignored by client
            await asyncio.sleep(0.5)     # poll interval

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
