import httpx
from dataclasses import asdict
from pathlib import Path
from egc import *
from . import schemas

class Client:
    def __init__(self, base_url="http://localhost:8000/api", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout = httpx.Timeout(30, read=600), # TODO what should these actually be?
        )

    async def aclose(self):
        await self._c.aclose()

    async def config(self):
        resp = await self._c.get("/config")
        resp.raise_for_status()
        return resp.json()

    async def node_status(self):
        resp = await self._c.get("/node/status")
        resp.raise_for_status()
        return resp.json()

    async def node_await(self):
        # TODO what's a good timeout here?
        # (the await call on the server will time out after 180 so far)
        resp = await self._c.get("/node/await")
        resp.raise_for_status()

    async def election_subscribe(self, election_cfg: ElectionConfig):
        data = schemas.ElectionSubscribe(config=election_cfg)
        resp = await self._c.put('/election/subscribe', json=data.model_dump())
        resp.raise_for_status()

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
        resp = await self._c.post('/election/create', json = data.model_dump())
        resp.raise_for_status()

    async def election_events(self, filter: str|None = None):
        async with self._c.stream("GET", "/election/events") as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                 if line.startswith("data:"): # SSE event
                     line = line[5:].strip()
                     event_dict = json.loads(line)
                     event = ElectionEvent.from_dict(event_dict)
                     if (not filter) or (filter.lower() in str(event).lower()):
                        yield event
                     if event.event_type in ['end election', 'burn test tokens', 'timed out']:
                         return

    async def election_burntesttokens(self):
        resp = await self._c.post('/election/burntesttokens')
        resp.raise_for_status()

    # TODO two different fns here and they create the WalletLoadOrCreate?
    async def wallet_load_or_create(self, data: schemas.WalletLoadOrCreate):
        "Load a wallet from sk_dict, or create one if empty."
        resp = await self._c.put('/wallet', json=data.model_dump())
        resp.raise_for_status()

    async def wallet_show(self):
        resp = await self._c.get('/wallet')
        resp.raise_for_status()
        return resp.json()

    async def wallet_clear(self):
        resp = await self._c.delete('/wallet')
        resp.raise_for_status()
        return resp.json()

    async def wallet_save(self):
        # Differs from wallet show in that this includes the (private) signing key.
        resp = await self._c.get('/wallet/save')
        resp.raise_for_status()
        return resp.json()

    async def phase_get(self):
        resp = await self._c.get('/phase')
        resp.raise_for_status()
        return resp.json()

    async def collateral_return(self, return_addr: Optional[str] = None):
        data = schemas.CollateralReturn(return_addr=return_addr)
        resp = await self._c.post('/collateral/return', json=data.model_dump())
        resp.raise_for_status()

    async def collateral_await(self) -> str:
        resp = await self._c.get('/collateral/await')
        resp.raise_for_status()

    async def channel_await(self, role: str) -> str:
        data = schemas.ChannelAwait(role=role)
        resp = await self._c.get('/channel/await', params=data.model_dump(mode='json', exclude_none=True))
        resp.raise_for_status()
        out = schemas.ChannelAwaitOut.model_validate(resp.json())
        return out.channel_str

    async def ceremony(self):
        resp = await self._c.get('/ceremony')
        resp.raise_for_status()
        return resp.json()

    async def ceremony_create(self, ceremony: CeremonyDetails):
        data = schemas.CeremonyCreate(
            number_of_guardians = ceremony.number_of_guardians,
            quorum = ceremony.quorum,
        )
        resp = await self._c.post('/ceremony/create', json=data.model_dump())
        resp.raise_for_status()

    async def records_list(self) -> list[PublicRecordMetadata]:
        resp = await self._c.get("/records") # TODO /list?
        resp.raise_for_status()
        recs = schemas.RecordsListOut.model_validate(resp.json())
        return recs

    async def records_drop(self, indexes: list[int]):
        data = schemas.RecordsDrop(indexes_to_drop=indexes)
        resp = await self._c.request(
            'DELETE',
            '/records',
            json=data.model_dump()
        )
        resp.raise_for_status()

    async def records_post(
            self,
            indexes: list[int],
            min_size: int = 1,
            max_size: int = 10, # TODO tune for traced contract first
            advance_phase: Optional[str] = None
        ):
        data = schemas.RecordsPost(
            indexes_to_post = indexes,
            min_size        = min_size,
            max_size        = max_size,
            advance_phase   = advance_phase,
        )
        resp = await self._c.post('/records/post', json=data.model_dump())
        resp.raise_for_status()

    async def records_await(self, timeout: int) -> str:
        data = schemas.RecordsAwait(timeout=timeout) # TODO same params for all `await` cmds?
        resp = await self._c.get('/records/await', params=data.model_dump(mode='json', exclude_none=True))
        resp.raise_for_status()

    async def manifest_create(self, manifest: EgcManifest):
        manifest_dict = manifest.to_dict()
        LOG.debug(f'manifest dict: {manifest_dict}')
        resp = await self._c.post('/manifest', json=manifest_dict)
        resp.raise_for_status()
