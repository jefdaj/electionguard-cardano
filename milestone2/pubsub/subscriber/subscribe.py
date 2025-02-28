#!/usr/bin/env python3

import asyncio
import json
import os
import sys
import time

from os.path import join, dirname, exists
from tempfile import TemporaryDirectory
import aioipfs


# these come from arion-compose.nix
IPFS_HTTP_PORT = int(os.environ['IPFS_HTTP_PORT'])
IPFS_DATA_DIR = os.environ['IPFS_DATA_DIR']

# TODO if you make this a bind mount it'll appear automatically, right?
os.makedirs(IPFS_DATA_DIR, exist_ok=True)


def watch_file_for_cids(path: str):
    # quick hack to test the downloader before the cardano stuff exists
    # watches for changes to ${IPFS_DATA_DIR}/new_cids.txt and yields them
    prev_mtime = 0
    while True:
        time.sleep(5)
        if not exists(path):
            # touch it
            # TODO remove?
            with open(path, 'w') as f:
                f.write()
        cur_mtime = os.stat(path).st_mtime
        if cur_mtime == prev_mtime:
            continue
        with open(path, 'r') as f:
            for line in f.readlines():
                cid = line.strip()
                if len(cid) > 0:
                    yield cid
        prev_mtime = cur_mtime


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
    out_path = join(IPFS_DATA_DIR, js['path'] + '.json')
    os.makedirs(dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(js['content'], f)
    print(f'wrote {cid} to {out_path}')


if __name__ == '__main__':
    new_cids_path = sys.argv[1]
    loop = asyncio.new_event_loop()
    try:
        for cid in watch_file_for_cids(new_cids_path):
            loop.run_until_complete(
                get_json(cid)
            )
    except KeyboardInterrupt:
        pass
