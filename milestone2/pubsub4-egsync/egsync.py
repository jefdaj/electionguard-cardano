#!/usr/bin/env python3

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

from flask import Flask, jsonify, render_template_string, request, abort
from os import makedirs
from os.path import basename, dirname, join, exists
from pathlib import Path
from pprint import pprint
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
app = Flask(__name__)
info = app.logger.info


### environment vars ###

# TODO should these handle failure?
IPFS_API_ADDR = os.environ['IPFS_API_ADDR']; info(f'IPFS_API_ADDR: {IPFS_API_ADDR}')
MOCKCHAIN_JSON_DIR = os.environ['MOCKCHAIN_JSON_DIR']; info(f'MOCKCHAIN_JSON_DIR: {MOCKCHAIN_JSON_DIR}')
PUBLIC_RECORDS_DIR = os.environ['PUBLIC_RECORDS_DIR']; info(f'PUBLIC_RECORDS_DIR: {PUBLIC_RECORDS_DIR}')


### ipfs ###

# TODO write this/move code here

# IPFS_API = sys.argv[1]
# IPFS_CLIENT = ipfshttpclient.connect(addr=IPFS_API)
# info(f'ipfs client: {IPFS_CLIENT}')

# TODO cid type?
def publish_on_ipfs(path: str) -> str:
    res = IPFS_CLIENT.add(path)
    cid = res['Hash']
    IPFS_CLIENT.pin.add(cid)
    return cid

# TODO how to post a list of records rather than just one? need some kind of queue?
# TODO cid type?
def post_onchain(onchain_channel: str, record_type: str, cid: str, **fmtargs):
    channel_path = join(ONCHAIN_DIR, onchain_channel + '.json')
    post_json = {
        'action': 'post_public_record',
        'record_type': record_type,
        'cid': cid,
        **fmtargs
    }
    with open(channel_path, 'a') as f:
        json.dump(post_json, f)
        # TODO need a newline or anything?

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
        self.channel_state = {'admin': 0}

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
            return handler(obj)
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

def fetch_public_record(obj):
    info(f'fetch_public_record {obj}')
    # TODO write this... in pubsub4?

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

def handle_posted_json(obj):
    info(f'handle_posted_json new obj: {obj}')

# def ipfs_sync_loop():
#     """
#     Background loop that periodically fetches CIDs and pins them.
#     """
#     # TODO should there be a sync loop per channel?
#     info("Starting IPFS sync loop")
#     # client = ipfshttpclient.connect(addr=IPFS_API_ADDR)

    # watch_jsonl(join(ONCHAIN_DIR, 'admin1.jsonl'), handle_posted_json)

#     while True:
#         try:
#             cids = fetch_cids_from_provider()
#             new_cids = [cid for cid in cids if cid not in state["pinned_cids"]]
# 
#             for cid in new_cids:
#                 try:
#                     pin_cid(client, cid)
#                     state["pinned_cids"].add(cid)
#                 except Exception as e:
#                     msg = f"Error pinning {cid}: {e}"
#                     app.logger.error(msg)
#                     state["sync_errors"].append(msg)
# 
#             state["last_sync"] = time.time()
#         except Exception as e:
#             msg = f"Sync error: {e}"
#             app.logger.error(msg)
#             state["sync_errors"].append(msg)
# 
#         time.sleep(CID_POLL_INTERVAL)


### local records ###

# TODO is this a reasonable way to pass it? if not, use env
# TODO better naming convention now that the "public" dir is private?
PRIVATE_DIR = '/data/private'
info(f'PRIVATE_DIR: {PRIVATE_DIR}')

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

# TODO put public in the name
def record_basename(record_type:str, **fmtargs):
    'So far, only used to simplify verifier summary json keys'
    (_, _, fstr) = PUBLIC_RECORDS[record_type]
    fname = fstr.format(**fmtargs)
    return fname

# you probably want the public/private specialized versions below
def record_path(records_map, root_dir:str, record_type: str, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(root_dir, dname)
    makedirs(dpath, exist_ok=True) # TODO make the dir here?
    fname = fstr.format(**fmtargs)
    return join(dpath, fname + '.json')

# you probably want the public or private versions below
def to_record(records_map, record_type: str, obj, **fmtargs) -> str:
    (dname, fstr) = records_map[record_type]
    dpath = join(PRIVATE_DIR, dname)
    makedirs(dpath, exist_ok=True)
    fname = fstr.format(**fmtargs)
    # serialize.to_file(obj, fname, dpath)
    fpath = join(dpath, fname + '.json')
    # TODO is this right? nothing special?
    with open(fpath, 'w') as f:
        json.dump(obj, f)
    print(f'dumped {record_type} to {fpath}')
    return fpath

# you probably want the public or private versions below
# TODO separate into the json part (here) and the typed part (still in util.py?)
def from_record(records_map, record_type: str, **fmtargs):
    (dname, fstr) = records_map[record_type]
    dpath = join(PRIVATE_DIR, dname)
    fname = fstr.format(**fmtargs) + '.json'
    fpath = join(dpath, fname)

    # This returns a Python object of the correct type,
    # but for the API we need JSON.
    # TODO have another step for converting the reply to the type
    # return serialize.from_file(rtype, fpath)
    return json.load(fpath)

# TODO separate the code for actually saving the file from the ipfs code
# TODO would it be better to save to a temporary location and let ipfs put the file in place?
def to_public_record(
        onchain_channel: str,
        record_type: str,
        obj,
        **fmtargs
    ):
    # TODO if adding the file fails, what then? remove locally? retry?
    fpath = to_record(PUBLIC_RECORDS, record_type, obj, **fmtargs)
    cid = publish_on_ipfs(fpath)
    post_onchain(onchain_channel, record_type, cid, **fmtargs)
    # TODO return something? cid, bool, res

def from_public_record(record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, record_type, **fmtargs)


### flask routes ###

INDEX_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>egsync</title>
  <!-- htmx from CDN; you can vendor it if you prefer -->
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
</head>
<body>
  <h1>egsync</h1>
</body>
</html>
"""

# TODO remove?
@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)

# @app.route("/api/status")
# def status():
#     return jsonify(
#         pinned_cids=sorted(list(state["pinned_cids"])),
#         last_sync=state["last_sync"],
#         sync_errors=state["sync_errors"][-10:],  # last 10 errors
#     )


# @app.route("/api/pin", methods=["POST"])
# def api_pin():
#     cid = request.form.get("cid") or request.json.get("cid") if request.is_json else None
#     if not cid:
#         return ("Missing 'cid'", 400)
# 
#     try:
#         client = ipfshttpclient.connect(addr=IPFS_API_ADDR)
#         pin_cid(client, cid)
#         state["pinned_cids"].add(cid)
#     except Exception as e:
#         app.logger.error(f"Manual pin error for {cid}: {e}")
#         return (f"Error pinning {cid}: {e}", 500)
# 
#     # For htmx, return HTML snippet, but also reasonable for plain browser.
#     return f"<p>Pinned CID: <code>{cid}</code></p>"

# TODO add an arg or url part for channel
@app.route("/api/public_records/<record_type>", methods=["POST"])
def save_public_record(record_type):
    print(f'save_public_record record_type: {record_type}')

    # 1. Validate record_type
    if record_type not in PUBLIC_RECORDS:
        abort(404, description=f"Unknown record_type '{record_type}'")

    # rtype, _, _ = PUBLIC_RECORDS[record_type]

    # 2. Require JSON
    if not request.is_json:
        abort(400, description="Expected JSON body")

    raw = request.get_json()

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
    fmtargs = request.args.to_dict()

    try:
        onchain_channel = fmtargs.pop('onchain_channel')
    except:
        abort(400, description="Expected onchain_channel")

    # 5. Delegate file-writing to your helper
    # TODO and then append to the channel jsonl in here?
    to_public_record(onchain_channel, record_type, raw, **fmtargs)

    return "", 204

@app.route("/api/public_records/<record_type>", methods=["GET"])
def load_public_record(record_type):
    if record_type not in PUBLIC_RECORDS:
        abort(404, description=f"Unknown record_type '{record_type}'")

    rtype, _, _ = PUBLIC_RECORDS[record_type]
    fmtargs = request.args.to_dict()

    try:
        obj = from_public_record(PRIVATE_DIR, record_type, **fmtargs)
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

if __name__ == "__main__":
    # Start background sync thread, then run Flask dev server
    start_background_thread()
    app.run(host="0.0.0.0", port=5000, debug=True)
