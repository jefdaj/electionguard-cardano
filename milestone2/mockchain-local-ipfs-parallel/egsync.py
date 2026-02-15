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
from glob import glob

import string
from typing import Dict, Callable, Pattern, Any

from aiohttp import ClientConnectorError, ClientConnectorDNSError

import tempfile
import random

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

def from_record(records_map, record_type: str, **fmtargs) -> str:
    (dname, fstr) = records_map[record_type]
    dpath = join(PUBLIC_RECORDS_DIR, dname)
    fname = fstr.format(**fmtargs) + '.json'
    fpath = join(dpath, fname)

    # This returns json text rather than json for use with serialize.from_raw
    with open(fpath, 'r') as f:
        return f.read()

def parse_paths(
    fmt: str,
    paths,
    field_patterns: Dict[str, str] | None = None,
    converters: Dict[str, Callable[[str], Any]] | None = None,
    suffix: str = r'\.json$',
):
    """
    Parse a list of paths according to `fmt`, returning list[dict].
    """
    converters = converters or {}
    regex = format_to_regex(fmt, field_patterns=field_patterns, suffix=suffix)

    results = []
    for p in paths:
        m = regex.match(p)
        if not m:
            continue
        d = m.groupdict()
        for k, fn in converters.items():
            if k in d:
                d[k] = fn(d[k])
        results.append(d)
    return results

def list_record_fmtargs(record_type):
    (fdir, fbase) = PUBLIC_RECORDS[record_type]
    fstr = join(PUBLIC_RECORDS_DIR, fdir, fbase)
    gstr = re.sub('{.*?}', '*', fstr)
    paths = sorted(glob(gstr))
    # TODO move converters to PUBLIC_RECORDS as a new field?
    default_converters = {
        'backup_order': int,
        'device_number': int,
    }
    fmtargs = parse_paths(fstr, paths, converters=default_converters)
    return fmtargs


### ipfs ###

async def wait_for_ipfs(ipfs, timeout=10):
    end = asyncio.get_event_loop().time() + timeout
    while True:
        try:
            await ipfs._client.version()  # raw client, single call
            return
        except (ClientConnectorError, ClientConnectorDNSError):
            if asyncio.get_event_loop().time() > end:
                raise
            await asyncio.sleep(1)

class RetryingIPFS:
    def __init__(self, client, retries=10, delay=1.0, backoff=1.5):
        self._client = client
        self._retries = retries
        self._delay = delay
        self._backoff = backoff

    async def _retry(self, coro_factory):
        delay = self._delay
        for attempt in range(self._retries):
            try:
                await wait_for_ipfs(self) # TODO make it a method?
                return await coro_factory()
            except (ClientConnectorError, ClientConnectorDNSError) as e:
                if attempt == self._retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay *= self._backoff

    # Wrap only what you need, e.g. add, cat, pin, etc.
    async def add(self, *args, **kwargs):
        kwargs.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add(*args, **kwargs))

    async def add_json(self, *args, **kwargs):
        kwargs.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add_json(*args, **kwargs))

    async def cat(self, *args, **kwargs):
        return await self._retry(lambda: self._client.cat(*args, **kwargs))

    @property
    def pin(self):
        client_pin = self._client.pin

        class _PinProxy:
            def __init__(_self, outer, inner):
                _self._outer = outer
                _self._inner = inner

            async def add(_self, *args, **kwargs):
                return await _self._outer._retry(
                    lambda: _self._inner.add(*args, **kwargs)
                )

            async def rm(_self, *args, **kwargs):
                return await _self._outer._retry(
                    lambda: _self._inner.rm(*args, **kwargs)
                )

            def __getattr__(_self, name):
                return getattr(_self._inner, name)

        return _PinProxy(self, client_pin)

    # Fallback for anything else – no retries by default:
    def __getattr__(self, name):
        return getattr(self._client, name)

# TODO separate the code for actually saving the file from the ipfs code
# TODO would it be better to save to a temporary location and let ipfs put the file in place?
async def to_public_record(
        ipfs: RetryingIPFS,
        channel: str,
        record_type: str,
        obj,
        **fmtargs
    ):
    # TODO if adding the file fails, what then? remove locally? retry?
    fpath = to_record(PUBLIC_RECORDS, record_type, obj, **fmtargs)
    cid = await publish_on_ipfs(ipfs, obj)
    fmtargs['cid'] = cid
    mockchain_post_public_record(channel, record_type, **fmtargs)
    # TODO return something? cid, bool, res

def from_public_record(record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, record_type, **fmtargs)

def format_to_regex(
    fmt: str,
    field_patterns: Dict[str, str] | None = None,
    suffix: str = r'\.json$',
) -> Pattern:
    """
    Turn a format string like
      '.../{guardian_id}_backup_{backup_order}'
    into a regex with named groups.

    `field_patterns` can override the pattern for specific fields.
    """
    formatter = string.Formatter()
    field_patterns = field_patterns or {}

    regex_parts = []

    for literal_text, field_name, format_spec, conversion in formatter.parse(fmt):
        # Escape literal parts
        if literal_text:
            regex_parts.append(re.escape(literal_text))

        if field_name is None:
            continue  # no more fields

        # Pattern for this field: custom or default
        pat = field_patterns.get(field_name, r'[^/]+')
        regex_parts.append(f"(?P<{field_name}>{pat})")

    # Add optional suffix, e.g. file extension
    if suffix:
        regex_parts.append(suffix)

    return re.compile("".join(regex_parts))

async def fetch_cid_to_file(ipfs: RetryingIPFS, cid: str, filename: str):
    # Get the raw bytes for the CID
    data = await ipfs.cat(cid)

    # Ensure parent dir exists
    dir_name = os.path.dirname(filename) or "."
    os.makedirs(dir_name, exist_ok=True)

    # Create a temp file in the same directory
    fd, tmp_path = tempfile.mkstemp(
        dir=dir_name,
        prefix=".tmp_",
        suffix=".part"
    )
    os.close(fd)  # we'll reopen it with aiofiles

    try:
        # Write to temp file
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(data)
            await f.flush()

        # Atomically replace the target file
        os.replace(tmp_path, filename)
    finally:
        # Clean up temp file if anything went wrong before replace
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

async def publish_on_ipfs(ipfs: RetryingIPFS, obj: dict) -> str:
    added_file = await ipfs.add_json(obj)
    cid = added_file['Hash'] # TODO is this a dict in this aioipfs version?
    # TODO does this also need to be wrapped in retry logic? or is that not important?
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
def mockchain_post_public_record(channel: str, record_type: str, **post_json):
    post_json['record_type'] = record_type
    mockchain_post_json(channel, 'post_public_record', **post_json)

def mockchain_mint_channel(channel: str, new_channel_name: str, **post_json):
    post_json['new_channel_name'] = new_channel_name
    mockchain_post_json(channel, 'mint_channel', **post_json)

def mockchain_post_json(channel: str, action_type: str, **post_json):
    json_path = next_json_path(channel)
    info(f'json_path: {json_path}')
    post_json['action'] = action_type
    makedirs(dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(post_json, f) # TODO pydantic here?

async def fetch_public_record(ipfs: RetryingIPFS, obj):
    info(f'fetch_public_record {obj}')
    record_type = obj.pop('record_type')
    cid = obj.pop('cid')
    fpath = record_path(PUBLIC_RECORDS, PUBLIC_RECORDS_DIR, record_type, **obj)
    await fetch_cid_to_file(ipfs, cid, fpath)


### mockchain ###


def jitter_delay(max_seconds=1):
    time.sleep(random.uniform(0, max_seconds))

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
            'mint_channel': self.mint_channel
            # TODO close channels too?
        }
        self.mockchain_event_handlers.update(mockchain_event_handlers)

        # map of valid channels -> index of latest json parsed from that channel
        self.channel_state = {'admin_1': 0}

    def on_created(self, event):
        self.on_fs_event(event)

    def on_modified(self, event):
        self.on_fs_event(event)

    def on_fs_event(self, event):
        args = self.mockchain_event_args(event)
        if args is not None:
            jitter_delay() # prevent all IPFS containers doing IO at once
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

    def mint_channel(self, obj: dict):
        info(f'mint_channel {obj}')
        new_channel = obj['new_channel_name']
        new_channel_dir = join(self.mockchain_dir, new_channel)
        makedirs(new_channel_dir, exist_ok=True)
        if new_channel in self.channel_state.keys():
            raise Exception(f'new_channel already exists: {new_channel}')
        self.channel_state[new_channel] = 0


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

@app.route("/api/channels", methods=["POST"])
async def mint_channel():
    fmtargs = request.args.to_dict()
    info(f'mint_channel {fmtargs}')
    try:
        sender_channel = fmtargs.pop('channel')
    except:
        abort(400, description="Expected sender channel")
    try:
        new_channel_name = fmtargs.pop('new_channel_name')
    except:
        abort(400, description="Expected new channel_name")
    # TODO actually do stuff here
    info(f'mint_channel new_channel_name: {new_channel_name}')
    mockchain_mint_channel(sender_channel, new_channel_name, **fmtargs)
    return "", 204

# TODO add an arg or url part for channel
@app.route("/api/public_records/<record_type>", methods=["POST"])
async def save_public_record(record_type):

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
    fmtargs = request.args.to_dict()
    info(f'save_public_record {record_type} {fmtargs} {raw}')

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
    info(f'load_public_record {record_type} {fmtargs}')

    try:
        return from_public_record(record_type, **fmtargs)
    except Exception as e:
        print(e)
        abort(404, description="Record not found")


# TODO should this be an official part of your electionguard protocol?
@app.route("/api/record_fmtargs/<record_type>", methods=["GET"])
async def record_fmtargs(record_type):
    """Returns a list of dicts with fmtargs for all records of a given type.
    """
    try:
        (_, _) = PUBLIC_RECORDS[record_type]
    except KeyError:
        abort(404, description="Record not found")
    fmtargs = list_record_fmtargs(record_type)
    info(f'record_fmtargs {record_type} -> {fmtargs}')
    return jsonify(fmtargs)

### main ###

@app.before_serving
async def startup():
    # Get the main asyncio loop used by Quart/Hypercorn
    loop = asyncio.get_running_loop()

    # TODO any reason this needs to be global now?
    # TODO is the client actually trying to connect to localhost:5001 instead of the other container?
    # TODO maybe the difference is dns4 vs ip4? ask ai
    # TODO also see if you can add a test call that always runs and waits until a response before continuing
    ipfs_client = RetryingIPFS(AsyncIPFS(maddr=IPFS_API_ADDR)); info(f'ipfs_client: {ipfs_client}')
    # await wait_for_ipfs(ipfs_client)

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
