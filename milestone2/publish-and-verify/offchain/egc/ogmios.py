# TODO rename node everywhere?

import asyncio
import json
import websockets

from typing import Any, Dict
from pycardano import OgmiosV6ChainContext, Network

# TODO load these from somewhere?

OGMIOS_HOST = "localhost"
OGMIOS_PORT = 1337
OGMIOS_CTX = OgmiosV6ChainContext(
    host=OGMIOS_HOST,
    port=OGMIOS_PORT,
    network=Network.TESTNET
)

# TODO rename to make it more obvious this is for the --since args?
# TODO and also to check if ogmios is up I guess
async def query_network_tip() -> dict:
    # TODO is there an equivalent context function?
    url = f"ws://{OGMIOS_HOST}:{OGMIOS_PORT}"
    async with websockets.connect(url) as ws:
        request = {
            "jsonrpc": "2.0",
            "method": "queryNetwork/tip",
            "params": {},
            "id": "get-network-tip",
        }
        await ws.send(json.dumps(request))
        raw = await ws.recv()
        response = json.loads(raw)

        if "error" in response:
            raise RuntimeError(f"Ogmios error: {response['error']}")

        # Newer Ogmios: result is directly the point: { "slot": ..., "id": ... }
        result = response.get("result")
        if not isinstance(result, dict) or "slot" not in result or "id" not in result:
            raise RuntimeError(f"Unexpected Ogmios response: {response}")

        # make it more obvious for my kupo --since use case
        slot = result["slot"]
        result["block_hash"] = result["id"]
        del result["id"]
        return result
        # return json.dumps(result, indent=2)

# TODO what's the proper idiom for this?
def query_network_tip_sync() -> dict:
    return asyncio.run(query_network_tip())
