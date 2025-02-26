#!/usr/bin/env python3

import sys
import asyncio
import aioipfs
from os import makedirs

# see arion-compose.nix for ports
# TODO load a common config json there and in python
IPFS_HTTP_PORT = 5002

IPFS_DATA_DIR = './data'
makedirs(IPFS_DATA_DIR, exist_ok=True)

async def get(cid: str):
    client = aioipfs.AsyncIPFS(maddr=f'/ip4/127.0.0.1/tcp/{IPFS_HTTP_PORT}')
    await client.get(cid, dstdir=IPFS_DATA_DIR)
    await client.close()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    while True:
        try:
            cid = input('Next CID to download: ').strip()
            if len(cid) == 0:
                continue
            loop.run_until_complete(
                get(cid)
            )
        except KeyboardInterrupt:
            print()
            print('ok, done')
            break
