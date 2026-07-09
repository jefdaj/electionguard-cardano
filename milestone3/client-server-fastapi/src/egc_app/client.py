import httpx

class Client:
    def __init__(self, base_url="http://localhost:8000/api", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(base_url=base_url, transport=transport)

    async def health(self):
        r = await self._c.get("/health")
        r.raise_for_status()
        return r.json()

    async def set_trivial(self, n):
        r = await self._c.post(f"/trivial/{n}")
        r.raise_for_status()
        return r.json()

    async def get_trivial(self):
        r = await self._c.get("/trivial")
        r.raise_for_status()
        return r.json()

    async def subscribe(self, policy_id, slot_no, block_header_hash):
        r = await self._c.post(f'/subscribe/{policy_id}/{slot_no}/{block_header_hash}')
        r.raise_for_status()
        return r.json()
