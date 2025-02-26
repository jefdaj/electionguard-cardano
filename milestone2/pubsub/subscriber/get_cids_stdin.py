#!/usr/bin/env python3

import sys
import asyncio
import aioipfs
from os import makedirs

DATA_DIR = './data'
makedirs(DATA_DIR, exist_ok=True)

async def get(cid: str):
    client = aioipfs.AsyncIPFS(maddr='/ip4/127.0.0.1/tcp/5001')
    await client.get(cid, dstdir=DATA_DIR)
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
