import httpx

class Client:
    def __init__(self, base_url="http://localhost", transport=None):
        # transport lets you point at a unix socket or ASGI app in tests
        self._c = httpx.AsyncClient(base_url=base_url, transport=transport)

    async def incr(self):
        r = await self._c.post("/incr")
        r.raise_for_status()
        return r.json()

    async def status(self):
        r = await self._c.get("/status")
        r.raise_for_status()
        return r.json()
