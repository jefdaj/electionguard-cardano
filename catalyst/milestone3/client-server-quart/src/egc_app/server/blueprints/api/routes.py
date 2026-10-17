from . import api
from quart import current_app
from werkzeug.exceptions import Conflict
from egc import *

@api.get('/health')
async def health():
    return {'status': 'ok'}

@api.get('/state')
async def state():
    return {'state': current_app.state}

@api.post('/incr/<int:n>')
async def incr(n):
    current_app.state += n
    return await state()

@api.post("/subscribe/<policy_id>/<int:slot_no>/<block_header_hash>")
async def subscribe(policy_id, slot_no, block_header_hash):
    if current_app.subscriber is not None:
        raise Conflict("Already have a subscriber")
    sub_cfg = SubscriberConfig(
        since_slot=slot_no,
        since_block_hash=block_header_hash,
        policy_id=ScriptHash(bytes.fromhex(policy_id))
    )
    LOG.debug(f'sub_cfg: {sub_cfg}')
    current_app.subscriber = ElectionSubscriber(sub_cfg, on_event=lambda e: print(e))
    current_app.subscriber.start()
    return {}
