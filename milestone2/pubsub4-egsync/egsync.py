#!/usr/bin/env python3

import aiofiles
import aioipfs
import asyncio
import json
import logging
import os
import re
import requests
import sys
import threading
import time

# from flask import Flask, jsonify, render_template_string, request, abort
from aioipfs import AsyncIPFS
from quart import Quart, request, abort, jsonify
from hypercorn.config import Config
from hypercorn.asyncio import serve
from os import makedirs
from os.path import basename, dirname, join, exists
from pathlib import Path
from typing import List, Callable, TextIO
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


### logging ###

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler("/tmp/egsync.log"),
        logging.StreamHandler()
    ]
)

# TODO start app later and just init logger on its own here?
app = Quart(__name__)
info = app.logger.info


### environment vars ###

# TODO should these handle failure?
IPFS_API_ADDR      = os.environ['IPFS_API_ADDR']     ; info(f'IPFS_API_ADDR: {IPFS_API_ADDR}')
MOCKCHAIN_JSON_DIR = os.environ['MOCKCHAIN_JSON_DIR']; info(f'MOCKCHAIN_JSON_DIR: {MOCKCHAIN_JSON_DIR}')
PUBLIC_RECORDS_DIR = os.environ['PUBLIC_RECORDS_DIR']; info(f'PUBLIC_RECORDS_DIR: {PUBLIC_RECORDS_DIR}')


### local records ###

# TODO should egsync be converting to/from these types? or delegating that to egpy?
# TODO can there be one source of truth for this in all scripts?
# TODO actually though, egpy only needs to know the types right?
# TODO wait do we NOT need the types here? and not need to have electionguard installed?
PUBLIC_RECORDS = {
    'manifest': (
        # Manifest,
        '1_config/1_announce',
        '1_manifest'
    ),
    'ceremony_details': (
        # CeremonyDetails,
        '1_config/1_announce',
        '2_ceremony'
    ),
    'guardian_pubkey': (
        # ElectionPublicKey,
        '1_config/2_ceremony/1_pubkeys',
        '{guardian_id}'
    ),
    'guardian_backup': (
        # ElectionPartialKeyBackup,
        '1_config/2_ceremony/2_backups',
        '{guardian_id}_backup_{backup_order}'
    ),
    'guardian_verification': (
        # ElectionPartialKeyVerification,
        '1_config/2_ceremony/3_verifications',
        '{guardian_id}_backup_{backup_order}'
    ),
    'joint_key': (
        # ElectionJointKey,
        '1_config/3_election',
        'joint_key'
    ),
    'constants': (
        # ElectionConstants,
        '1_config/3_election',
        'constants'
    ),
    'context': (
        # CiphertextElectionContext,
        '1_config/3_election',
        'context'
    ),
    'device': (
        # EncryptionDevice,
        '1_config/4_devices',
        'device_{device_number}'
    ),
    'ballot_submitted': (
        # CiphertextBallot, # TODO SubmittedBallot with state set to UNKNOWN?
        '2_ballots/1_submitted',
        '{ballot_id}'
    ),
    'cast_notice': (
        # CastNotice,
        '2_ballots/2_cast',
        '{ballot_id}'
    ),
    'ballot_spoiled': (

        # This seems correct to me even though it doesn't match the
        # electionguard-python implementation: we *do* want to publish all
        # the nonces at this step, right? So people can decrypt immediately
        # rather than waiting for the guardians.
        # CiphertextBallot,

        '2_ballots/3_spoiled',
        '{ballot_id}'
    ),
    'ciphertext_tally': (
        # PublishedCiphertextTally, # TODO CiphertextTally? (the non-"published" version)
        '3_results',
        '1_tally'
    ),
    'tally_share': (
        # DecryptionShare,
        '3_results/2_decrypt/1_shares/1_tally',
        'tally_{guardian_id}'
    ),
    'spoiled_share': (
        # DecryptionShare,
        '3_results/2_decrypt/1_shares/2_spoiled',
        '{spoiled_id}_{guardian_id}'
    ),
    # TODO rename tally_result?
    'plaintext_tally': (
        # PlaintextTally,
        '3_results/2_decrypt/2_combined',
        '1_tally'
    ),
    'spoiled_result': (
        # PlaintextTally,
        '3_results/2_decrypt/2_combined/2_spoiled',
        '{ballot_id}'
    ),
    'summary': (
        # dict,
        '4_verify',
        '{verifier_id}'
    ),
}

def record_path(records_map, root_dir:str, record_type: str, **fmtargs):
    (dname, fstr) = records_map[record_type]
    dpath = join(root_dir, dname)
    makedirs(dpath, exist_ok=True) # TODO make the dir here?
    fname = fstr.format(**fmtargs)
    return join(dpath, fname + '.json')

def to_record(records_map, record_type: str, obj, **fmtargs) -> str:
    fpath = record_path(PUBLIC_RECORDS, PUBLIC_RECORDS_DIR, record_type, **fmtargs)
    with open(fpath, 'w') as f:
        json.dump(obj, f)
    info(f'saved {record_type} to {fpath}')
    return fpath

# TODO separate into the json part (here) and the typed part (still in util.py?)
def from_record(records_map, record_type: str, **fmtargs):
    (dname, fstr) = records_map[record_type]
    dpath = join(PUBLIC_RECORDS_DIR, dname)
    fname = fstr.format(**fmtargs) + '.json'
    fpath = join(dpath, fname)

    # This returns a Python object of the correct type,
    # but for the API we need JSON.
    # TODO have another step for converting the reply to the type
    # return serialize.from_file(rtype, fpath)
    return json.load(fpath)

# TODO separate the code for actually saving the file from the ipfs code
# TODO would it be better to save to a temporary location and let ipfs put the file in place?
async def to_public_record(
        ipfs: AsyncIPFS,
        channel: str,
        record_type: str,
        obj,
        **fmtargs
    ):
    # TODO if adding the file fails, what then? remove locally? retry?
    fpath = to_record(PUBLIC_RECORDS, record_type, obj, **fmtargs)
    # cid = asyncio.run(
    cid = await publish_on_ipfs(ipfs, obj)
    # )
    mockchain_post_public_record(channel, record_type, cid, **fmtargs)
    # TODO return something? cid, bool, res

def from_public_record(record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, record_type, **fmtargs)


### ipfs ###

async def fetch_cid_to_file(ipfs: AsyncIPFS, cid: str, filename: str):
    # Get the raw bytes for the CID
    data = await ipfs.cat(cid)
    # Save to your chosen filename
    # TODO if there are issues with lots of fs events, save to a tmpdir and move atomically instead
    async with aiofiles.open(filename, "wb") as f:
        await f.write(data)

async def publish_on_ipfs(ipfs: AsyncIPFS, obj: dict) -> str:
    added_file = await ipfs.add_json(obj)
    cid = added_file['Hash'] # TODO is this a dict in this aioipfs version?
    ipfs.pin.add(cid) # TODO await?
    return cid

# TODO should this go through MockchainSubscriber instead? or is separate more robust?
def next_json_path(channel: str) -> str:
    channel_dir = join(MOCKCHAIN_JSON_DIR, channel)
    index = 1
    while True:
        json_path = join(channel_dir, f'{index:03d}.json')
        if not exists(json_path):
            return json_path
        index += 1

# TODO how to post a list of records rather than just one? need some kind of queue?
# TODO cid type?
def mockchain_post_public_record(channel: str, record_type: str, cid: str, **fmtargs):
    json_path = next_json_path(channel)
    info(f'json_path: {json_path}')
    post_json = {
        'action': 'post_public_record',
        'record_type': record_type,
        'cid': cid,
        **fmtargs
    }
    makedirs(dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(post_json, f) # TODO pydantic here?

async def fetch_public_record(ipfs: AsyncIPFS, obj):
    info(f'fetch_public_record {obj}')
    cid = obj.pop('cid')
    record_type = obj.pop('record_type')
    fpath = record_path(PUBLIC_RECORDS, PUBLIC_RECORDS_DIR, record_type, **obj)
    await fetch_cid_to_file(ipfs, cid, fpath)


### mockchain ###

class MockchainSubscriber(FileSystemEventHandler):
    def __init__(self, loop, mockchain_dir,
                 debounce_seconds=1.0, mockchain_event_handlers={},
                 *args, **kwargs):
        info('init MockchainSubscriber')
        super().__init__(*args, **kwargs)

        self.mockchain_dir = mockchain_dir

        # For delayed responses
        self.loop = loop
        self.debounce_seconds = debounce_seconds

        # (channel, index) -> concurrent.futures.Future
        self.pending_events = {}

        # map of action name -> callback
        # callbacks should accept an event object
        self.mockchain_event_handlers = {
            'new_mockchain_channel': self.new_mockchain_channel
            # TODO close channels too?
        }
        self.mockchain_event_handlers.update(mockchain_event_handlers)

        # map of valid channels -> index of latest json parsed from that channel
        self.channel_state = {'admin1': 0}

    def on_created(self, event):
        self.on_fs_event(event)

    def on_modified(self, event):
        self.on_fs_event(event)

    def on_fs_event(self, event):
        args = self.mockchain_event_args(event)
        if args is not None:
            try:
                self.schedule_response(**args)
            except Exception as e:
                info(e)

    def subscribed_json_regex(self):
        return (
            '^' +
            self.mockchain_dir +
            '/([^/]*)'
            '/([0-9]{3,3}).json$'
        )

    def subscribed_json_path(self, channel: str, index: int) -> str:
        return join(self.mockchain_dir, channel, f'{index:03d}.json')

    def next_json_index(self, channel_name):
        "What should be the index of the next event?"
        return self.channel_state[channel_name] + 1

    def mockchain_event_args(self, event):
        try:
            match = re.match(self.subscribed_json_regex(), event.src_path)
            return {
                'channel': match.group(1),
                'index': int(match.group(2))
            }
        except Exception as e:
            # info(f'{event} -> {e}')
            return None

    def schedule_response(self, channel: str, index: int):
        info(f'schedule_response {channel} {index}')

        args = (channel, index)

        # Cancel existing pending response if any
        future = self.pending_events.get(args)
        if future is not None and not future.done():
            future.cancel()

        async def delayed_response():
            await asyncio.sleep(self.debounce_seconds)
            await self.on_mockchain_event(*args)
            self.pending_events.pop(args, None)

        future = asyncio.run_coroutine_threadsafe(
            delayed_response(),
            self.loop,
        )
        self.pending_events[args] = future

    async def on_mockchain_event(self, channel: str, index: int):
        if not channel in self.channel_state.keys():
            raise Exception(f'invalid mockchain_channel {channel}')
        expected = self.next_json_index(channel)
        if index != expected:
            msg = f'invalid index for {channel} channel: got {index}, should be {expected}'
            raise Exception(msg)
        self.channel_state[channel] += 1
        obj = self.parse_mockchain_json(channel, index)
        # info(obj)

        try:
            action = obj['action']
            handler = self.mockchain_event_handlers[action]
        except KeyError:
            info(f'error: unknown action {action} in {obj}')
            return

        try:
            # handler can be sync or async
            result = handler(obj)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            info(f'error handling {obj}: {e}')

    def parse_mockchain_json(self, channel: str, index: int) -> dict:
        parsed = {'mockchain_channel': channel, 'mockchain_index': index}
        path = self.subscribed_json_path(channel, index)
        with open(path, 'r') as f:
            parsed.update(json.load(f))
        return parsed

    def new_mockchain_channel(self, obj: dict):
        info(f'new_mockchain_channel {obj}')
        channel = obj['new_channel_name']
        channel_dir = join(self.mockchain_dir, channel)
        makedirs(channel_dir, exist_ok=True)
        if channel in self.channel_state.keys():
            raise Exception(f'channel already exists: {channel}')
        self.channel_state[channel] = 0


### flask routes ###

# INDEX_TEMPLATE = """
# <!doctype html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>egsync</title>
#   <!-- htmx from CDN; you can vendor it if you prefer -->
#   <script src="https://unpkg.com/htmx.org@1.9.12"></script>
# </head>
# <body>
#   <h1>egsync</h1>
# </body>
# </html>
# """

# TODO remove?
# @app.route("/")
# async def index():
#     return render_template_string(INDEX_TEMPLATE)

# TODO add an arg or url part for channel
@app.route("/api/public_records/<record_type>", methods=["POST"])
async def save_public_record(record_type):
    info(f'save_public_record record_type: {record_type}')

    # 1. Validate record_type
    if record_type not in PUBLIC_RECORDS:
        abort(404, description=f"Unknown record_type '{record_type}'")

    # 2. Require JSON
    if not request.is_json:
        abort(400, description="Expected JSON body")

    raw = await request.get_json()

    # 3. Convert JSON → Python object using your serialization layer
    # Adjust these helpers to whatever electionguard.serialize actually provides.
    #
    # Possibilities in many codebases:
    #   obj = serialize.from_dict(rtype, raw)
    #   obj = rtype.from_dict(raw)
    #   obj = serialize.object_from_raw(rtype, raw)
    #
    # I'll write this as a placeholder:
    # obj = serialize.from_raw(rtype, raw)

    # 4. Extra format args come from query params (guardian_id, ballot_id, etc.)
    fmtargs = request.args.to_dict() # TODO await?
    info(f'save_public_record fmtargs: {fmtargs}')

    try:
        channel = fmtargs.pop('channel')
    except:
        abort(400, description="Expected channel")

    # 5. Delegate file-writing to your helper
    await to_public_record(app.ipfs_client, channel, record_type, raw, **fmtargs)

    return "", 204

@app.route("/api/public_records/<record_type>", methods=["GET"])
async def load_public_record(record_type):
    if record_type not in PUBLIC_RECORDS:
        abort(404, description=f"Unknown record_type '{record_type}'")

    fmtargs = request.args.to_dict()
    info(f'load_public_record fmtargs: {fmtargs}')

    try:
        obj = from_public_record(PUBLIC_RECORDS_DIR, record_type, **fmtargs)
    except FileNotFoundError:
        abort(404, description="Record not found")

    # Convert Python object → JSON-serializable structure
    #
    # Again, adapt to your real helpers:
    #   raw = serialize.to_dict(obj)
    #   raw = obj.to_dict()
    # raw = serialize.to_dict(obj)
    # return jsonify(raw)

    raw = serialize.to_raw(obj)
    return raw


### main ###

@app.before_serving
async def startup():
    # Get the main asyncio loop used by Quart/Hypercorn
    loop = asyncio.get_running_loop()

    # TODO any reason this needs to be global now?
    # TODO is the client actually trying to connect to localhost:5001 instead of the other container?
    # TODO maybe the difference is dns4 vs ip4? ask ai
    # TODO also see if you can add a test call that always runs and waits until a response before continuing
    ipfs_client = AsyncIPFS(maddr=IPFS_API_ADDR); info(f'ipfs_client: {ipfs_client}')

    mockchain_dir = 'data/mockchain'
    os.makedirs(mockchain_dir, exist_ok=True)

    # I think these can be sync or async functions? Haven't tried sync yet.
    handlers = {
        'post_public_record': lambda obj: fetch_public_record(ipfs_client, obj),
    }

    observer = Observer()
    subscriber = MockchainSubscriber(
        loop=loop,
        mockchain_dir=mockchain_dir,
        mockchain_event_handlers=handlers,
    )
    observer.schedule(subscriber, path=mockchain_dir, recursive=True)
    observer.start()

    # Keep references so we can stop cleanly later
    app.mockchain_observer = observer
    app.mockchain_subscriber = subscriber
    app.ipfs_client = ipfs_client

@app.after_serving
async def shutdown():
    # Stop the observer on shutdown
    observer = getattr(app, "mockchain_observer", None)
    if observer is not None:
        observer.stop()
        observer.join()
    ipfs_client = getattr(app, "ipfs_client", None)
    if ipfs_client is not None:
        await ipfs_client.close()

async def main():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.workers = 1 # TODO remove for production?
    await serve(app, config)

if __name__ == "__main__":
    time.sleep(10) # TODO does this help connect to ipfs?
    asyncio.run(main())
