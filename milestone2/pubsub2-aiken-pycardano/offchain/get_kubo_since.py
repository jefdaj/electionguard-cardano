#!/usr/bin/env python3

# Get the current slot number + block hash from Ogmios to pass when starting
# Kupo. This code should be called *before* deploying a new pubsub contract to
# make sure that we can't miss the first transaction.

import argparse
import asyncio
import json
import sys
from typing import Any, Dict

import websockets

DEFAULT_OGMIOS_HOST = "localhost"
DEFAULT_OGMIOS_PORT = 1337


async def query_network_tip(host: str, port: int) -> Dict[str, Any]:
    url = f"ws://{host}:{port}"
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

        return result  # {"slot": ..., "id": ...}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Get current tip (slot, block hash) from Ogmios."
    )
    p.add_argument("--host", default=DEFAULT_OGMIOS_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_OGMIOS_PORT)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    try:
        tip = asyncio.run(query_network_tip(args.host, args.port))
    except Exception as e:
        print(f"Error talking to Ogmios: {e}", file=sys.stderr)
        sys.exit(1)

    slot = tip["slot"]
    tip["block_hash"] = tip["id"]
    del tip["id"]

    print(json.dumps(tip, indent=2))


if __name__ == "__main__":
    main()
