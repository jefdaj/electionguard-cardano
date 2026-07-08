import httpx

class Client:
    def __init__(self, base_url="http://localhost:5000/api", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(base_url=base_url, transport=transport)

    async def incr(self, n):
        r = await self._c.post(f"/incr/{n}")
        r.raise_for_status()
        return r.json()

    async def state(self):
        r = await self._c.get("/state")
        r.raise_for_status()
        return r.json()
