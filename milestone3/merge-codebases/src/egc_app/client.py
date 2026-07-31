import httpx
from dataclasses import asdict
from pathlib import Path
from egc import *
from . import schemas

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

    async def node_status(self):
        r = await self._c.get("/node/status")
        r.raise_for_status()
        return r.json()

    async def node_await(self):
        # TODO what's a good timeout here?
        # (the await call on the server will time out after 180 so far)
        r = await self._c.get("/node/await", timeout=httpx.Timeout(600, read=None))
        r.raise_for_status()
        # return r.json()

    async def election_subscribe(self, election_cfg: ElectionConfig):
        data = schemas.ElectionSubscribe(config=election_cfg)
        r = await self._c.put('/election/subscribe', json=data.model_dump())
        r.raise_for_status()

    async def election_create(
            self,
            funder_sk: SigningKey,
            admin_vkh: VerificationKeyHash,
            admin_ada: int = 100,
        ):
        data = schemas.ElectionCreate(
            funder_sk = funder_sk,
            admin_vkh = admin_vkh,
            admin_ada = admin_ada,
        )
        r = await self._c.post('/election/create', json=data.model_dump())
        r.raise_for_status()

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

    async def election_burntesttokens(self):
        r = await self._c.post('/election/burntesttokens')
        r.raise_for_status()

    # TODO two different fns here and they create the WalletLoadOrCreate?
    async def wallet_load_or_create(self, data: schemas.WalletLoadOrCreate):
        "Load a wallet from sk_dict, or create one if empty."
        r = await self._c.put('/wallet', json=data.model_dump())
        r.raise_for_status()
        # return r.json() # TODO remove?

    async def wallet_show(self):
        r = await self._c.get('/wallet')
        r.raise_for_status()
        return r.json()

    async def wallet_clear(self):
        r = await self._c.delete('/wallet')
        r.raise_for_status()
        return r.json()

    async def wallet_save(self):
        r = await self._c.get('/wallet/save')
        r.raise_for_status()
        return r.json()

    async def phase_get(self):
        r = await self._c.get('/phase')
        r.raise_for_status()
        return r.json()

    async def collateral_return(self):
        r = await self._c.post('/collateral/return') # TODO .delete?
        r.raise_for_status()
