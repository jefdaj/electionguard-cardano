#!/usr/bin/env python3

import json
import sys
import asyncio
import aioipfs
import time
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pprint import pprint
from typing import List

# see arion-compose.nix
# pprint(os.environ)
IPFS_API_ADDR = os.environ['IPFS_API_ADDR']


LAST_CIDS_WRITTEN = datetime.now()


def announce_new_cids(cids: List[str], path: str):
    # debounce: if writing a bunch of things too fast, append instead
    # then the subscriber can deduplicate as needed and not miss anything
    now = datetime.now()
    global LAST_CIDS_WRITTEN
    if (now - LAST_CIDS_WRITTEN).total_seconds() < 5:
        write_mode = 'a'
    else:
        write_mode = 'w'
    LAST_CIDS_WRITTEN = now
    with open(path, write_mode) as f:
        for cid in cids:
            f.write(cid + '\n')
    print(f'wrote {len(cids)} CIDs to {path}')


# TODO more specific return type?
def wrapped_json_with_path(actual_path: str, virtual_path: str) -> dict:
    with open(actual_path, 'r') as f:
        content = json.load(f)
    js = {
        'path': virtual_path,
        'content': content,
        'uploaded_at': str(datetime.now()) # just for uniqueness
    }
    return js


async def upload_and_announce_json(actual_path: str, virtual_path: str, new_cids_path: str):
    client = aioipfs.AsyncIPFS(maddr=IPFS_API_ADDR)
    js = wrapped_json_with_path(actual_path, virtual_path)
    kwargs = {
        # 'recursive': False,
        # 'progress' : True,   # TODO False?
        'pin'      : True,   # this is the default
        # 'input_enc': 'json', # this is the default
    }
    added_file = await client.add_json(js, **kwargs)
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
        virtual_path = os.path.splitext(
            os.path.relpath(path, self.upload_dir)
        )[0]
        # print('upload:', locals())
        try:
            self.loop.run_until_complete(
                upload_and_announce_json(
                    path, virtual_path, self.new_cids_path
                )
            )
        except Exception as e:
            print(e)
            raise

    def on_created(self, event):
        path = event.src_path
        if not os.path.isfile(path):
            return
        print(f'File {path} has been created')
        self.upload(path)

    def on_modified(self, event):
        path = event.src_path
        if not os.path.isfile(path):
            return
        print(f'File {path} has been modified')
        self.upload(path)


if __name__ == '__main__':
    upload_dir    = sys.argv[1]
    os.makedirs(upload_dir, exist_ok=True)
    new_cids_path = sys.argv[2]
    loop = asyncio.new_event_loop()
    observer = Observer()
    uploader = UploadNewFiles(loop, upload_dir, new_cids_path)
    observer.schedule(uploader, path=upload_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except: # TODO sigint?
        observer.stop()
    observer.join()
