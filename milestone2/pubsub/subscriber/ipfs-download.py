#!/usr/bin/env python3

import json
import sys
import asyncio
import aioipfs
from tempfile import TemporaryDirectory
from os import makedirs
from os.path import join, dirname


# TODO get these from arion var
IPFS_HTTP_PORT = 5002
SYNC_DIR = './data'


async def get(cid: str, dstdir: str):
    client = aioipfs.AsyncIPFS(maddr=f'/ip4/127.0.0.1/tcp/{IPFS_HTTP_PORT}')
    await client.get(cid, dstdir=dstdir)
    await client.close()


async def get_json(cid: str):
    # TODO is there a cleaner way? this seems very hacky
    with TemporaryDirectory() as tmp_dir:
        await get(cid, dstdir=tmp_dir)
        get_path = join(tmp_dir, cid)
        with open(get_path, 'r') as f:
            js = json.load(f)
    # TODO extend protocol to include the extension and allow non-json files?
    out_path = join(SYNC_DIR, js['path'] + '.json')
    makedirs(dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(js['content'], f)
    print(f'wrote {cid} to {out_path}')


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    while True:
        try:
            cid = input('Next CID to download: ').strip()
            if len(cid) == 0:
                continue
            loop.run_until_complete(
                get_json(cid)
            )
        except KeyboardInterrupt:
            print()
            print('ok, done')
            break
