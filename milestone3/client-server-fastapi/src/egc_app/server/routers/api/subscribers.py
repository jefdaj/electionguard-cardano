from fastapi import APIRouter, Depends, Request
from egc_app.server.deps import get_state
# from egc_app.server.schemas.election import ElectionOut
from egc import *
import asyncio
import json
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["subscriber"])

# TODO rename subscriber -> election? observer?

@router.post("/subscribers", status_code=201)
# async def start_subscriber(policy_id: str, slot_no: int, header_hash: str, state=Depends(get_state)):
async def start_subscriber(sub_cfg_dict: dict, state=Depends(get_state)):

    # So far there's only ever one subscriber running at a time. But we call it
    # subscribers here 1) in case we want multiple later, and 2) to enforce that you
    # have to post args for the subscriber before you can get the corresponding
    # events.

    # Enforce the only one election thing.
    if state.subscriber is not None:
        return 409 # TODO proper idiom?

    # TODO proper auto-decode here
    sub_cfg = SubscriberConfig(
        since_slot = sub_cfg_dict['since_slot'],
        since_block_hash = sub_cfg_dict['since_block_hash'],
        policy_id = ScriptHash(bytes.fromhex(sub_cfg_dict['policy_id'])),
    )

   # TODO integrate on_event with fastapi logging
    state.subscriber = ElectionSubscriber(sub_cfg, on_event=lambda e: print(e))
    state.subscriber.start()

    return ElectionOut(policy_id=policy_id)

@router.get("/subscribers/{policy_id}/events") # TODO response model?
async def stream_events(policy_id: str, request: Request, state=Depends(get_state)):

    if state.subscriber is None:
        raise HTTPException(404)

    sub_cfg = state.subscriber.config
    script_hash = ScriptHash(bytes.fromhex(policy_id))
    if not script_hash == sub_cfg.policy_id:
        raise HTTPException(409) # TODO proper idiom?

    async def gen():
        sent = 0
        while True:
            if await request.is_disconnected():
                break
            events = state.subscriber.all_election_events()   # full list, grows over time
            for event in events[sent:]:     # only the new tail
                yield f"data: {json.dumps(event, default=str)}\n\n" # TODO fix ScriptHash json thing?
            sent = len(events)
            await asyncio.sleep(0.5)         # poll interval

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
