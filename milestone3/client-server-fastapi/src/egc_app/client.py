import httpx
from dataclasses import asdict
from egc import *

class Client:
    def __init__(self, base_url="http://localhost:8000/api", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(base_url=base_url, transport=transport)

    async def aclose(self):
        await self._c.aclose()

    async def health(self):
        r = await self._c.get("/health")
        r.raise_for_status()
        return r.json()

    async def set_trivial(self, n):
        r = await self._c.put(f"/trivial/{n}")
        r.raise_for_status()
        return r.json()

    async def get_trivial(self):
        r = await self._c.get("/trivial")
        r.raise_for_status()
        return r.json()

    async def subscribe(self, policy_id, slot_no, block_header_hash):
        # r = await self._c.post(f'/subscribe/{policy_id}/{slot_no}/{block_header_hash}')

        # TODO proper auto encode/decode of actual SubscriberConfig (policy_id is sticking point)
        sub_cfg_dict = {
            'since_slot'      : slot_no,
            'since_block_hash': block_header_hash,
            'policy_id'       : policy_id,
        }

        r = await self._c.post('/subscriber', json=sub_cfg_dict)
        r.raise_for_status()
        return r.json()

    async def observe(self):
        url = "/subscriber/events"
        async with self._c.stream("GET", url, timeout=httpx.Timeout(5.0, read=None)) as r:
            async for line in r.aiter_lines():
                 if line.startswith("data:"): # SSE event
                     line = line[5:].strip()
                     event_dict = json.loads(line)
                     event = ElectionEvent.from_dict(event_dict)
                     yield event
                     if event.event_type == 'burn test tokens':
                         return
                     if event.event_type == 'end election':
                         return
