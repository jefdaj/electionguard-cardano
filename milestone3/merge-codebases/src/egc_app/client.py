import httpx
from dataclasses import asdict
from egc import *

class Client:
    def __init__(self, base_url="http://localhost:8000/api", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(base_url=base_url, transport=transport)

    async def aclose(self):
        await self._c.aclose()

    async def config(self):
        r = await self._c.get("/config")
        r.raise_for_status()
        return r.json()

    async def status(self):
        r = await self._c.get("/status")
        r.raise_for_status()
        return r.json()

    async def election_subscribe(self, sub_cfg: SubscriberConfig):
        r = await self._c.put('/election', json=asdict(sub_cfg))
        r.raise_for_status()
        return r.json()

    async def election_events(self, filter: str|None = None):
        url = "/election/events"
        async with self._c.stream("GET", url, timeout=httpx.Timeout(5.0, read=None)) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                 if line.startswith("data:"): # SSE event
                     line = line[5:].strip()
                     event_dict = json.loads(line)
                     event = ElectionEvent.from_dict(event_dict)
                     if (not filter) or (filter.lower() in str(event).lower()):
                        yield event
                     if event.event_type == 'burn test tokens':
                         return
                     if event.event_type == 'end election':
                         return

    async def wallet_load_or_create(self, name: str, sk_dict: dict | None = None):
        "Load a wallet from sk_dict, or create one if empty."
        r = await self._c.put('/wallet', json={'name': name, 'sk_dict': sk_dict})
        r.raise_for_status()
        return r.json() # TODO remove?

    async def wallet_show(self):
        r = await self._c.get('/wallet')
        r.raise_for_status()
        return r.json()

    async def wallet_clear(self):
        r = await self._c.post('/wallet/clear')
        r.raise_for_status()
        return r.json()
