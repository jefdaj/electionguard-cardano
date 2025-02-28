#!/usr/bin/env python3

import json
import sys
import asyncio
import aioipfs
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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


class UploadNewFiles(FileSystemEventHandler):
    def __init__(self, loop, upload_dir, new_cids_path, *args, **kwargs):
        super(UploadNewFiles, self).__init__(*args, **kwargs)
        self.loop = loop
        self.upload_dir = upload_dir
        self.new_cids_path = new_cids_path

    def upload(self, path: str):
        print('upload:', locals())
        return
        # actual_path = 
        # virtual_path = 
        self.loop.run_until_complete(
            upload_and_announce_json(actual_path, virtual_path, self.new_cids_path)
        )

    def on_created(self, event):
        print(f'File {event.src_path} has been created')
        self.upload(event.src_path)

    def on_modified(self, event):
        print(f'File {event.src_path} has been modified')
        self.upload(event.src_path)


if __name__ == '__main__':
    upload_dir    = sys.argv[1]
    new_cids_path = sys.argv[2]
    loop = asyncio.new_event_loop()
    observer = Observer()
    uploader = UploadNewFiles(loop, upload_dir, new_cids_path)
    observer.schedule(
        uploader,
        path=upload_dir,
        recursive=True
    )
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # while True:
    #     try:
    #         actual_path  = input('Actual path to a JSON file to upload: ').strip()
    #         if len(actual_path) == 0:
    #             print(f'invalid actual path "{actual_path}"')
    #             continue
    #         virtual_path = input('Path to put in IPFS JSON data: ').strip()
    #         if len(virtual_path) == 0:
    #             print(f'invalid virtual path "{virtual_path}"')
    #             continue
    #         loop.run_until_complete(
    #             upload_and_announce_json(actual_path, virtual_path, new_cids_path)
    #         )
    #     except KeyboardInterrupt:
    #         print()
    #         print('ok, done')
    #         break
