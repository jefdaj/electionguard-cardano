#!/usr/bin/env python3

import sys
import asyncio
import aioipfs
from os import makedirs
from os.path import basename
# from pprint import pprint

# see arion-compose.nix for ports
# TODO load a common config json there and in python
IPFS_HTTP_PORT = 5001


async def add_files(files: list):
    client = aioipfs.AsyncIPFS(maddr=f'/ip4/127.0.0.1/tcp/{IPFS_HTTP_PORT}')
    kwargs = {
        'recursive': False,
        'progress': True,
        'pin': True,
    }
    async for added_file in client.add(*files, **kwargs):
        print('{0} {1}'.format(added_file['Hash'], added_file['Name']))
    await client.close()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    while True:
        try:
            path = input('file to upload: ').strip()
            if len(path) == 0:
                continue
            loop.run_until_complete(
                add_files([path])
            )
        except KeyboardInterrupt:
            print()
            print('ok, done')
            break
