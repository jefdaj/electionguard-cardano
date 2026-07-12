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
async def start_subscriber(sub_cfg: SubscriberConfig, state=Depends(get_state)):

    # TODO proper auto-decode here
    # policy_id = ScriptHash(bytes.fromhex(sub_cfg_dict['policy_id']))
    # sub_cfg = SubscriberConfig(
    #     policy_id   = policy_id,
    #     since_slot  = sub_cfg_dict['since_slot'],
    #     since_block = sub_cfg_dict['since_block'],
    # )
    # sub_cfg = SubscriberConfig.from_qrcode_str(qrcode_str)

    # Reset election-specific state, leaving alone the config, wallet, etc
    reset_election_state(state)
    # TODO defaultdict or something to avoid this
    if not 'election' in state.config:
        state.config['election'] = {}
    state.config['election']['subscribe'] = asdict(sub_cfg)

    # TODO integrate on_event with fastapi logging
    state.subscriber = ElectionSubscriber(sub_cfg, on_event=lambda e: None)
    state.subscriber.start()

    return 201

@router.get("/events") # TODO response model?
async def stream_events(request: Request, state=Depends(get_state)):

    if state.subscriber is None:
        raise HTTPException(404)

    # sub_cfg = state.subscriber.config
    # script_hash = ScriptHash(bytes.fromhex(policy_id))
    # if not script_hash == sub_cfg.policy_id:
    #     raise HTTPException(409) # TODO proper idiom?

    async def gen():
        sent = 0
        while True:
            if await request.is_disconnected():
                break
            events = state.subscriber.all_election_events() # full list, grows over time
            # The data: and : (comment line) thing here is part of the SSE spec
            for event in events[sent:]:     # only the new tail
                yield f"data: {event.to_raw()}\n\n" # double newline dispatches SSE event
            sent = len(events)
            if len(events) == sent:      # nothing new
                yield ": keepalive\n\n"  # comment line, ignored by client
            await asyncio.sleep(0.5)     # poll interval

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
