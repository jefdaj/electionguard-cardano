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
from quart import Quart, request, abort, jsonify
from hypercorn.config import Config
from hypercorn.asyncio import serve
from os import makedirs
from os.path import basename, dirname, join, exists
from pathlib import Path
from typing import List, Callable, TextIO
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from pprint import pprint


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
    info(f'dumped {record_type} to {fpath}')
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
        channel: str,
        record_type: str,
        obj,
        **fmtargs
    ):
    # TODO if adding the file fails, what then? remove locally? retry?
    fpath = to_record(PUBLIC_RECORDS, record_type, obj, **fmtargs)
    # cid = asyncio.run(
    cid = await publish_on_ipfs(obj)
    # )
    mockchain_post_public_record(channel, record_type, cid, **fmtargs)
    # TODO return something? cid, bool, res

def from_public_record(record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, record_type, **fmtargs)


### ipfs ###

IPFS_CLIENT = aioipfs.AsyncIPFS(maddr=IPFS_API_ADDR); info(f'IPFS_CLIENT: {IPFS_CLIENT}')

async def fetch_cid_to_file(cid: str, filename: str):
    async with aioipfs.AsyncIPFS() as client:
        # Get the raw bytes for the CID
        data = await client.cat(cid)
    # Save to your chosen filename
    # TODO if there are issues with lots of fs events, save to a tmpdir and move atomically instead
    async with aiofiles.open(filename, "wb") as f:
        await f.write(data)

async def publish_on_ipfs(obj: dict) -> str:
    added_file = await IPFS_CLIENT.add_json(obj)
    cid = added_file['Hash'] # TODO is this a dict in this aioipfs version?
    IPFS_CLIENT.pin.add(cid) # TODO await?
    return cid

# TODO should this go through MockchainSubscriber instead? or is separate more robust?
def next_json_path(channel: str) -> str:
    channel_dir = join(MOCKCHAIN_JSON_DIR, channel)
    if not exists(channel_dir):
        return 0 # TODO exception instead?
    index = 1
    while True:
        json_path = join(channel_dir, f'{index:03d}.json')
        if not exists(path):
            return path
        index += 1

# TODO how to post a list of records rather than just one? need some kind of queue?
# TODO cid type?
def mockchain_post_public_record(channel: str, record_type: str, cid: str, **fmtargs):
    print('locals:'); pprint(locals())
    json_path = next_json_path(channel)
    post_json = {
        'action': 'post_public_record',
        'record_type': record_type,
        'cid': cid,
        **fmtargs
    }
    with open(json_path, 'w') as f:
        json.dump(post_json, f) # TODO pydantic here?

async def fetch_public_record(obj):
    info(f'fetch_public_record {obj}')
    cid = obj['cid']
    record_type = obj['record_type']
    fpath = record_path(PUBLIC_RECORDS, PUBLIC_RECORDS_DIR, record_type, **fmtargs)
    await fetch_cid_to_file(cid, fpath)

# IPFS_API_ADDR = os.getenv("IPFS_API_ADDR", "/ip4/127.0.0.1/tcp/5001")
# CID_PROVIDER_URL = os.getenv("CID_PROVIDER_URL", "http://localhost:8080/cids")
# CID_POLL_INTERVAL = float(os.getenv("CID_POLL_INTERVAL", "30.0"))

# Global state for demo purposes; in real apps use something more robust.
# state = {
#     "pinned_cids": set(),
#     "last_sync": None,
#     "sync_errors": [],
# }

# def fetch_cids_from_provider() -> List[str]:
#     """
#     Fetch a list of CIDs from an external service.
#     Expected response: JSON list of strings, e.g. ["Qm...", "bafy..."].
#     """
#     resp = requests.get(CID_PROVIDER_URL, timeout=10)
#     resp.raise_for_status()
#     data = resp.json()
#     if not isinstance(data, list):
#         raise ValueError("CID provider must return a JSON list")
#     return [str(cid).strip() for cid in data if cid]

# def pin_cid(cid: str) -> None:
#     info(f"Pinning CID: {cid}")
#     IPFS_CLIENT.pin.add(cid)


### mockchain ###

class MockchainSubscriber(FileSystemEventHandler):
    def __init__(self, loop, mockchain_dir,
                 debounce_seconds=1.0, mockchain_event_handlers={},
                 *args, **kwargs):
        info('init MockchainSubscriber')
        super(MockchainSubscriber, self).__init__(*args, **kwargs)

        self.mockchain_dir = mockchain_dir

        # map of action name -> callback
        # callbacks should accept an event object
        self.mockchain_event_handlers = {
            'new_mockchain_channel': self.new_mockchain_channel
            # TODO close channels too?
        }
        self.mockchain_event_handlers.update(mockchain_event_handlers)

        # map of valid channels -> index of latest json parsed from that channel
        self.channel_state = {'admin1': 0}

        # for json files that may be partially written or just have multiple fs events
        self.debounce_seconds = debounce_seconds
        self.pending_events = {} # path -> asyncio.Handle?
        # TODO also handle when the events are done but the ipfs file hasn't propagated
        # TODO self.newjson_callback or similar

        # For delayed responses
        self.loop = loop

    def on_created(self, event):
        return self.on_fs_event(event)

    def on_modified(self, event):
        return self.on_fs_event(event)

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

        # Cancel existing pending response if any
        args = (channel, index)
        if args in self.pending_events:
            self.pending_events[args].cancel()

        async def delayed_response():
            await asyncio.sleep(self.debounce_seconds)
            await self.on_mockchain_event(*args)
            self.pending_events.pop(args, None)

        # Use call_soon_threadsafe to schedule from another thread
        future = asyncio.run_coroutine_threadsafe(
            delayed_response(),
            self.loop
        )
        self.pending_events[args] = future

    def on_mockchain_event(self, channel: str, index: int):
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
            return asyncio.run_coroutine_threadsafe(
                handler(obj),
                self.loop
            )
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

def mockchain_subscribe_loop():
    mockchain_dir = 'data/mockchain' # TODO pass arg
    os.makedirs(mockchain_dir, exist_ok=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    observer = Observer() # TODO what does this do?
    handlers = {
        'post_public_record': fetch_public_record
    }
    subscriber = MockchainSubscriber(
        loop,
        mockchain_dir,
        mockchain_event_handlers=handlers
    )
    observer.schedule(subscriber, path=mockchain_dir, recursive=True)
    info('starting observer')
    try:
        observer.start()
        loop.run_forever()
    except:
        observer.stop()
        observer.join()
        loop.close()


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
    await to_public_record(channel, record_type, raw, **fmtargs)

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

# TODO move to mockchain section?
def start_background_thread():
    t = threading.Thread(target=mockchain_subscribe_loop, daemon=True)
    t.start()

async def main():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.workers = 1 # TODO remove for production?
    await server(app, config)

if __name__ == "__main__":
    # Start background sync thread, then run Flask dev server
    start_background_thread()
    app.run(host="0.0.0.0", port=5000, debug=True)
