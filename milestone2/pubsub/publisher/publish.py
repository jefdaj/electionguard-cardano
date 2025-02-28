#!/usr/bin/env python3

import json
import sys
import asyncio
import aioipfs
from os import makedirs
from os.path import basename
# from pprint import pprint
from typing import List

# see arion-compose.nix for ports
# TODO load a common config json there and in python
IPFS_HTTP_PORT = 5001


def write_cids_to_file(cids: List[str], path: str):
    with open(path, 'w') as f:
        for cid in cids:
            f.writeline(cid)


# TODO more specific return type?
def wrapped_json_with_path(actual_path: str, virtual_path: str) -> dict:
    with open(actual_path, 'r') as f:
        content = json.load(f)
    js = {
        'path': virtual_path,
        'content': content
    }
    return js


def announce_new_cids(cids: List[str], path: str):
    with open(path, 'r') as f:
        f.writelines(cids)
    print(f'wrote {len(cids)} CIDs to {path}')


async def upload_and_announce_json(actual_path: str, virtual_path: str, new_cids_path: str):
    client = aioipfs.AsyncIPFS(maddr=f'/ip4/127.0.0.1/tcp/{IPFS_HTTP_PORT}')
    js = wrapped_json_with_path(actual_path, virtual_path)
    # pprint(js)
    kwargs = {
        # 'recursive': False,
        # 'progress' : True,   # TODO False?
        'pin'      : True,   # this is the default
        # 'input_enc': 'json', # this is the default
    }
    added_file = await client.add_json(js, **kwargs)
    # pprint(added_file)
    # print(added_file['Hash'])
    new_cids = [added_file['Hash']]
    announce_new_cids(new_cids, new_cids_path)
    # print('{0} {1}'.format(added_file['Hash'], added_file['Name']))
    await client.close()


if __name__ == '__main__':
    new_cids_path = sys.argv[1]
    loop = asyncio.new_event_loop()
    while True:
        try:
            actual_path  = input('Actual path to a JSON file to upload: ').strip()
            if len(actual_path) == 0:
                print(f'invalid actual path "{actual_path}"')
                continue
            virtual_path = input('Path to put in IPFS JSON data: ').strip()
            if len(virtual_path) == 0:
                print(f'invalid virtual path "{virtual_path}"')
                continue
            loop.run_until_complete(
                upload_and_announce_json(actual_path, virtual_path, new_cids_path)
            )
        except KeyboardInterrupt:
            print()
            print('ok, done')
            break
