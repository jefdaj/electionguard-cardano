import click
import httpx
from dataclasses import asdict
from pathlib import Path
from egc import *
from . import schemas

# TODO clean this up
STATUS_MESSAGES = {
    404: ("Not found", 4),
    409: ("State conflict", 3),
}

def handle_http_errors(resp):
    "Handles printing and exiting cleanly on HTTP errors."
    if resp.is_success:
        return resp
    default_msg, code = STATUS_MESSAGES.get(resp.status_code, ("Request failed", 1))
    try:
        msg = resp.json().get("detail", default_msg)
    except ValueError:
        msg = default_msg
    err = click.ClickException(msg)
    err.exit_code = code
    raise err

class Client:
    def __init__(self, base_url="http://localhost:8000/api", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout = httpx.Timeout(900, read=900), # TODO what should these actually be?
        )

    async def aclose(self):
        await self._c.aclose()

    async def config(self):
        resp = await self._c.get("/config")
        return handle_http_errors(resp).json()

    async def node_status(self):
        resp = await self._c.get("/node/status")
        return handle_http_errors(resp).json()

    async def node_await(self):
        # TODO what's a good timeout here?
        # (the await call on the server will time out after 180 so far)
        resp = await self._c.get("/node/await")
        handle_http_errors(resp)

    async def election_subscribe(self, election_cfg: ElectionConfig):
        data = schemas.ElectionSubscribe(config=election_cfg)
        resp = await self._c.put('/election/subscribe', json=data.model_dump())
        handle_http_errors(resp)

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
        handle_http_errors(resp)

    async def election_events(self, filter: str|None = None):
        async with self._c.stream("GET", "/election/events") as resp:
            handle_http_errors(resp)
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
        handle_http_errors(resp)

    # TODO two different fns here and they create the WalletLoadOrCreate?
    async def wallet_load_or_create(self, data: schemas.WalletLoadOrCreate):
        "Load a wallet from sk_dict, or create one if empty."
        resp = await self._c.put('/wallet', json=data.model_dump())
        handle_http_errors(resp)

    async def wallet_show(self):
        resp = await self._c.get('/wallet')
        return handle_http_errors(resp).json()

    async def wallet_clear(self):
        resp = await self._c.delete('/wallet')
        return handle_http_errors(resp).json()

    async def wallet_save(self):
        # Differs from wallet show in that this includes the (private) signing key.
        resp = await self._c.get('/wallet/save')
        return handle_http_errors(resp).json()

    async def phase_get(self) -> EgcPhase:
        resp = await self._c.get('/phase')
        resp = handle_http_errors(resp)
        out = schemas.Phase.model_validate(resp.json())
        return EgcPhase(out.egc_phase_value)

    async def phase_await(self, phase: EgcPhase):
        data = schemas.Phase(egc_phase_value=phase.value)
        resp = await self._c.get('/phase/await', params=data.model_dump(mode='json', exclude_none=True))
        handle_http_errors(resp)

    async def phase_advance(self, new_phase: EgcPhase):
        data = schemas.Phase(egc_phase_value=new_phase.value)
        resp = await self._c.put('/phase', json=data.model_dump())
        handle_http_errors(resp)

    async def collateral_return(self, return_addr: Optional[str] = None):
        data = schemas.CollateralReturn(return_addr=return_addr)
        resp = await self._c.post('/collateral/return', json=data.model_dump())
        handle_http_errors(resp)

    async def collateral_await(self) -> str:
        resp = await self._c.get('/collateral/await')
        handle_http_errors(resp)

    async def channel_await(self, role: str) -> str:
        data = schemas.ChannelAwait(role=role)
        resp = await self._c.get('/channel/await', params=data.model_dump(mode='json', exclude_none=True))
        resp = handle_http_errors(resp)
        out = schemas.ChannelAwaitOut.model_validate(resp.json())
        return out.channel_str

    async def channel_create(
            self,
            requests: list[schemas.ChannelRequestOut],
            subchannel_ada: int,
            done_onboarding: bool,
        ):
        data = schemas.ChannelCreate(
            requests        = requests,
            ada_per_channel = subchannel_ada,
            done_onboarding = done_onboarding,
        )
        resp = await self._c.post('/channel/create', json=data.model_dump())
        handle_http_errors(resp)

    async def channel_request(self, role: str) -> schemas.ChannelRequestOut:
        data = schemas.ChannelRequest(requested_role=role)
        resp = await self._c.get(
            '/channel/request',
            params=data.model_dump(mode='json', exclude_none=True)
        )
        resp = handle_http_errors(resp)
        out = schemas.ChannelRequestOut.model_validate(resp.json())
        return out

    async def ceremony(self):
        resp = await self._c.get('/ceremony')
        resp = handle_http_errors(resp)
        return resp.json()

    async def ceremony_create(self, ceremony: CeremonyDetails):
        data = schemas.CeremonyDetails(
            number_of_guardians = ceremony.number_of_guardians,
            quorum = ceremony.quorum,
        )
        resp = await self._c.post('/ceremony/create', json=data.model_dump())
        handle_http_errors(resp)

    async def records_list(self) -> list[PublicRecordMetadata]:
        resp = await self._c.get("/records") # TODO /list?
        resp = handle_http_errors(resp)
        recs = schemas.RecordsListOut.model_validate(resp.json())
        return recs

    async def records_drop(self, indexes: list[int]):
        data = schemas.RecordsDrop(indexes_to_drop=indexes)
        resp = await self._c.request(
            'DELETE',
            '/records',
            json=data.model_dump()
        )
        handle_http_errors(resp)

    async def records_post(
            self,
            indexes: list[int],
            min_size: int = 1,
            max_size: int = 10, # TODO tune for traced contract first
            new_phase: Optional[EgcPhase] = None
        ):
        if new_phase:
            new_phase = schemas.Phase(egc_phase_value=new_phase.value)
        data = schemas.RecordsPost(
            indexes_to_post = indexes,
            min_size        = min_size,
            max_size        = max_size,
            new_phase       = new_phase,
        )
        resp = await self._c.post('/records/post', json=data.model_dump())
        handle_http_errors(resp)

    async def records_await(self, timeout: int) -> str:
        data = schemas.RecordsAwait(timeout=timeout) # TODO same params for all `await` cmds?
        resp = await self._c.get('/records/await', params=data.model_dump(mode='json', exclude_none=True))
        handle_http_errors(resp)

    async def manifest_create(self, manifest: EgcManifest):
        manifest_dict = manifest.to_dict()
        LOG.debug(f'manifest dict: {manifest_dict}')
        resp = await self._c.post('/manifest', json=manifest_dict)
        handle_http_errors(resp)

    async def ipfs_show(self):
        resp = await self._c.get('/ipfs') # TODO /ipfs_nodes?
        resp = handle_http_errors(resp)
        return resp.json()

    async def ipfs_post(
            self,
            explicit_hints: list[str],
            n_global_hints: int,
            n_local_hints: int,
        ):
        data = schemas.IpfsPost(
            explicit_hints = explicit_hints,
            n_global_hints = n_global_hints,
            n_local_hints  = n_local_hints,
        )
        resp = await self._c.put('/ipfs', json=data.model_dump()) # TODO /ipfs_nodes?
        handle_http_errors(resp)
