import argparse
import inspect
import itertools
import json
import os
import random
import requests
import signal
import socket
import subprocess
import sys
import threading
import time
import hashlib
import qrcode

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from os import environ
from pprint import pformat
from requests.adapters import HTTPAdapter
from typing import Any, Tuple, Optional, Self, Iterable
from urllib3.util.retry import Retry
from pydantic_core import to_jsonable_python

from .ogmios import *
from .plutus.types.channel import *
from .plutus.types.action import *
from .plutus.types.channel import *
from .election import ElectionConfig, ElectionContext
from .utils import safe_deepdiff

import logging
LOG = logging.getLogger(__name__)


def log_call(log_fn=LOG.debug):
    # Logs the name of the current function or method for debugging.
    log_fn(inspect.currentframe().f_back.f_code.co_qualname)

from pycardano import *


# TODO use https://pypi.org/project/kupo-py/ ?
# TODO assert that record metadata matches actual posting channel_id


# The port will be incremented if in use.
# TODO explicit config... pull from election.json or cli?
KUPO_HOST = environ.get('KUPO_HOST', '127.0.0.1')
KUPO_PORT = int(environ.get('KUPO_PORT', '1442'))


KUPO_POLL_SEC = 1
KUPO_MAX_CHECKPOINTS = 50


# TODO also use this in subscriberconfig?
@dataclass
class Point:
    slot_no: int
    header_hash: str

    def as_param(self) -> str:
        return f"{self.slot_no}.{self.header_hash}"

    # TODO from context instead?
    @classmethod
    def from_config(cls, data: ElectionConfig) -> Self:
        return cls(data.since_slot, data.since_block)

    @classmethod
    def from_kupo_headers(cls, headers: dict):
        slot = int(headers["X-Most-Recent-Checkpoint"])
        hhash = headers["ETag"]
        return cls(slot, hhash)


# These don't quite correspond to UTXOs because we store the state from the
# latest UTXO but the redeemer used to spend the previous UTXO on that channel.
# When a TX changes more than one channel, a ChannelEvent will be created for
# each one. For example: add or rm 3 channels -> 4 events.
@dataclass
class ChannelEvent:

    # TODO channel_event_id?
    id: str

    # Should always exist, and whenever there's both a spent and unspent match
    # the two should be equal. Used to remove history during rollbacks.
    slot_no: int

    # Should always exist. When one action/transaction touches multiple
    # channels, one event will be emitted per channel.
    channel_id: ChannelId

    # AKA redeemer. Should always exist. Can be used to infer which of the
    # input/output fields should have values below.
    action: ElectionAction

    # Mints have only outputs, burns have only inputs, and continuations have both.
    input_match:  Optional[dict[str, Any]]
    output_match: Optional[dict[str, Any]]

    # Mints have only outputs, burns have only inputs, and continuations have both.
    input_state:  Optional[ChannelState]
    output_state: Optional[ChannelState]

    # TODO add txid? where it comes from depends on start/middle/end


# TODO is there a cleaner way to do this?
def unique_id(*args, **kwargs) -> str:
    LOG.debug('unique_id')
    LOG.debug(f'kwargs: {kwargs}')
    args_str = str(args) + str(kwargs)
    LOG.debug(f'args_str: {args_str}')
    uniq_id = hashlib.md5(args_str.encode()).hexdigest()[:8]
    return uniq_id


@dataclass
class ElectionEvent:
    # The ChannelEvents above are for internal use; ElectionEvents are meant to
    # be the ones you'd want to display to users in a UI. One ChannelEvent
    # often corresponds to a list/set of ElectionEvents sharing the same tx_id
    # and slot_no.
    # TODO are ChannelEvents closer to transactions than events?
    # TODO what other fields should they have? see what the UI needs
    # TODO election_event_id?
    id: str
    tx_id: str
    slot_no: str
    channel: str
    event_type: str # TODO codify this once it's clearer
    event_desc: str # TODO codify this once it's clearer

    # TODO is this right?
    def to_raw(self) -> str:
        return json.dumps(to_jsonable_python(self))

    # TODO is this right?
    def to_json(self):
        return json.dumps(self)

    # TODO is this right?
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(**data)

def election_event(*args):
    ee_id = f'electionevent-{unique_id(*args)}'
    return ElectionEvent(ee_id, *args)


def election_events(event: ChannelEvent) -> list[ElectionEvent]:
    s = channel_id_to_string(event.channel_id)
    es = []
    ti = event_txid(event)
    sn = event.slot_no
    # add records
    if event.output_state:
        for record in event.output_state.state.new_records:
            e = election_event(ti, sn, s, 'post record', f'posted {record.metadata}')
            es.append(e)
    # add main action
    match event.action:
        case InitElection():
            e = election_event(ti, sn, 'funder', 'init election', 'authorized admin')
            es.append(e)
        case AdvancePhase():
            phase = event.output_state.state.phase
            e = election_event(ti, sn, s, 'advance phase', f'advanced to {phase}')
            es.append(e)
        case PostPublicRecords():
            pass # covered above
        case AddSubChannels(channels=cs):
            if s != 'admin':
                e = election_event(ti, sn, 'admin', 'add subchannel', f'authorized {s}')
                es.append(e)
        case RmSubChannels(channels=cs):
            if s != 'admin':
                e = election_event(ti, sn, 'admin', 'rm subchannel', f'revoked {s} authorization')
                es.append(e)
        case RebalanceFunds():
            pass # no user facing message needed?
        case EndElection():
            e = election_event(ti, sn, 'admin', 'end election', 'ended election')
            es.append(e)
        case _:
            raise NotImplemented

    # TODO where are these duplicates sneaking in?
    seen = set()
    es2 = []
    for e in es:
        if e.id in seen:
            LOG.warning(f'discard duplicate election event {e}')
        else:
            es2.append(e)
            seen.add(e.id)

    return es2


def event_txid(event: ChannelEvent):
    try:
        return event.input_match['spent_at']['transaction_id']
    except:
        return event.output_match['transaction_id']


# TODO move to channel_id.py
def channel_id_from_asset_name(encoded: str) -> ChannelId:
    log_call()
    channel_id = bytes.fromhex(encoded)
    # assert ChannelIdHelper.validate_bytes(channel_id)
    LOG.debug(f'decoded {asset_name} -> {channel_id}')
    return channel_id


# TODO where should this live?
# def channel_id_from_output(output: UTxO) -> Optional[ChannelId]:
#     for asset_key in output.value.assets.keys():
#         policy_id, asset_name = asset_key.split('.')
#         try:
#             return channel_id_from_asset_name(asset_name)
#         except:
#             continue
#     LOG.error(f'Output does not match any channel:\n{output}')
#     return None


# TODO where should this live?
def kupo_match_to_channel_str(kupo_match: dict) -> str:
    asset_hex = list(kupo_match['value']['assets'].keys())[0].split('.')[-1]
    asset_str = bytes.fromhex(asset_hex).decode()
    channel_str = asset_str.split('-')[-1] # TODO central to/from channel id fn would be less brittle
    return channel_str


# TODO where should this live?
def kupo_match_to_pycardano_utxo(kupo_dict: dict) -> UTxO:
    """Convert a Kupo UTXO response dict to a PyCardano UTxO.
    WARNING: Does not handle a lot of edge cases! Mainly for BurnTestTokens.
    """
    LOG.debug('kupo_match_to_pycardano_utxo')
    tx_input = TransactionInput.from_primitive(
        [kupo_dict["transaction_id"], kupo_dict["output_index"]]
    )

    coins = kupo_dict["value"]["coins"]
    assets = kupo_dict["value"].get("assets", {})

    if assets:
        multi_asset = MultiAsset()
        for asset_id, amount in assets.items():
            if "." in asset_id:
                policy_hex, asset_name_hex = asset_id.split(".", 1)
            else:
                policy_hex = asset_id
                asset_name_hex = ""

            policy_id = ScriptHash.from_primitive(policy_hex)
            asset_name = AssetName(bytes.fromhex(asset_name_hex))

            if policy_id not in multi_asset:
                multi_asset[policy_id] = Asset()  # <-- Asset(), not {}

            multi_asset[policy_id][asset_name] = amount

        value = Value(coin=coins, multi_asset=multi_asset)
    else:
        value = Value(coin=coins)

    address = Address.from_primitive(kupo_dict["address"])

    datum_hash = None
    if kupo_dict.get("datum_hash"):
        from pycardano import DatumHash
        datum_hash = DatumHash.from_primitive(kupo_dict["datum_hash"])

    tx_output = TransactionOutput(
        address=address,
        amount=value,
        datum_hash=datum_hash,
    )

    return UTxO(tx_input, tx_output)


# TODO where should this live?
def is_being_minted(channel_str: str, action: ElectionAction) -> bool:
    ch_id = coerce_channel_id(channel_str)
    match action:
        case AddSubChannels(channels=cs): return ch_id in cs
        case InitElection():              return ch_id == ADMIN_CHANNEL_ID
        case _:                           return False


# TODO where should this live?
def is_being_burned(channel_str: str, action: ElectionAction) -> bool:
    ch_id = coerce_channel_id(channel_str)
    match action:
        case BurnTestTokens():           return True
        case RmSubChannels(channels=cs): return ch_id in cs
        case EndElection():              return ch_id == ADMIN_CHANNEL_ID
        case _:                          return False


def _make_example_callback(callback_name: str):
    def fn(event: ChannelEvent) -> None:
        print(f'\n{callback_name} called with:\n{pformat(event)}')
    return fn


def _same_but_spent(old_event, new_event) -> bool:
    # TODO also allow the redeemer to change when a burn changes to spent? in case of diff ones per tx
    # TODO are the IDs reliable enough to go by exclusively now?
    # diff = safe_deepdiff(old_event, new_event)
    # changes = diff.get("type_changes", {})
    same_id = old_event.id == new_event.id
    old_unspent = \
        old_event.output_match is None \
        or old_event.output_match['spent_at'] is None
    new_unspent = \
        new_event.output_match is None \
        or new_event.output_match['spent_at'] is None
    return same_id and old_unspent and (not new_unspent)
#     try:
#         assert set(diff.keys()) == {"type_changes"}, f"Unexpected diff keys: {diff.keys()}"
#         assert len(changes) == 1, f"Expected 1 change, got: {changes}"
#         change = changes.get("root.output_match['spent_at']")
#         assert change is not None, "Expected spent_at to change"
#         assert change["old_value"] is None
#         assert isinstance(change["new_value"], dict)
#         assert old_event.id == new_event.id, f"old and new id should line up: {old_event}, {new_event}"
#         return True
#     except:
#         assert old_event.id != new_event.id, f"duplicate ids: {old_event}, {new_event}"
#         return False


# TODO where should this live?
def find_unused_port():
    # Returns a random(?) unused port number picked by the OS.
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


# TODO where should this live?
# TODO put the handling of "not a plutus constructor tag" here
# TODO use it instead of raw decode everywhere
def decode_action(redeemer_str):
    return decode_plutusdata_union(ElectionAction, redeemer_str)


def _make_session():
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.3, # 0.3, 0.6, 1.2, ...
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry,
    )
    s.mount("http://", adapter)
    s.headers.update({'Accept': 'application/json'})
    return s


class ElectionSubscriber:
    '''Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    '''


    def __init__(
            self,
            # config: ElectionConfig,
            election: ElectionContext,
            on_event    = _make_example_callback('on_event'),
            on_rollback = _make_example_callback('on_rollback'),
        ):

        log_call()

        # self.config = config # TODO remove in favor of context?
        self.election = election

        # Client callbacks, which default to printing events.
        self._on_election_event  = on_event
        self._client_on_rollback = on_rollback # TODO implement this

        # This is the main subscriber state; all the public methods read it,
        # and the internal callbacks mutate it.
        self._history: Mapping[ChannelId, list[ChannelEvent]] = {}

        # Lock when mutating history to prevent any potential weirdness.
        # RLock (as opposed to Lock) allows overlapping calls within the same thread.
        self._history_lock = threading.RLock()

        # for managing the kupo process
        self._kupo_proc:   Optional[subprocess.Popen] = None
        self._kupo_thread: Optional[threading.Thread] = None
        self._kupo_stop = threading.Event()

        self._kupo_port = KUPO_PORT

        # for http requests to the kupo process
        self._session = _make_session()

        # A list of matches we couldn't fit cleanly into an input/output pair to
        # make an event from. They'll be re-injected into the list of new
        # matches next poll.
        # TODO remove? not sure they're needed or helpful after all
        self._unpaired_matches = []

        # A list of slots + block header hashes Kupo reports that it indexed so far.
        # Used in case of rollbacks, for the If-None-Match ETag/304 mechanism.
        self._checkpoints: list[Point] = []


    ## query interface ##


    def all_channel_ids(self) -> list[ChannelId]:
        # Includes historical channels that have already been closed.
        # TODO return copies from all public methods
        log_call()
        with self._history_lock:
            return sorted(list(self._history.keys()))


    def current_channel_ids(self) -> list[ChannelId]:
        # TODO return copies from all public methods
        log_call()
        return [
            i for i in self.all_channel_ids()
            if self.current_state(i) is not None
        ]


    def all_history(self):
        log_call()
        with self._history_lock:
            return deepcopy(self._history)


    def channel_history(self, channel_id: ChannelId) -> list[ChannelEvent]:
        # Works fine on already-closed channels. Raises KeyError on not-yet-opened ones.
        # TODO return copies from all public methods
        log_call()
        with self._history_lock:
            return deepcopy(self._history[channel_id]) # TODO return None rather than raise KeyError?


    def current_utxo(self, channel_id: ChannelId) -> Optional[UTxO]:
        # Returns None if the channel hasn't been opened yet or was already closed
        # TODO return copies from all public methods
        log_call()
        try:
            event = self.channel_history(channel_id)[-1]
        except KeyError:
            return None
        match = event.output_match
        if match is None:
            return None
        else:
            return kupo_match_to_pycardano_utxo(match)


    def current_state(self, channel_id: ChannelId) -> Optional[ChannelState]:
        # Returns None if the channel hasn't been opened yet or was already closed
        # TODO return copies from all public methods
        log_call()
        try:
            with self._history_lock:
                event = self.channel_history(channel_id)[-1]
                return deepcopy(event.output_state) # may also be None
        except (KeyError, IndexError):
            return None


    def current_states(self) -> dict[str, Optional[ChannelState]]:
        # Closed channels are None.
        with self._history_lock:
            states = {}
            for ch_id in self.all_channel_ids():
                states[ch_id] = self.current_state(ch_id)
            return states


    def current_phase(self) -> ElectionPhase | str:
        log_call()
        # Returns None if the election hasn't started yet
        with self._history_lock:
            try:
                event = self.channel_history(ADMIN_CHANNEL_ID)[-1]
                return deepcopy(event.output_state.state.phase)
            except (KeyError, AttributeError):
                if self._history:
                    # None with history implies election ended
                    # TODO codify this in a better way!
                    return 'ElectionEnded'
                else:
                    # Otherwise, implies election hasn't started yet.
                    # TODO codify this in a better way!
                    return 'ElectionNotStarted'


    def wait_for_phase(self, phase: Optional[ElectionPhase], timeout=OGMIOS_TIMEOUT_SEC):
        # Poll until the election reaches the specified phase (or None)
        # TODO disambiguate None before vs after election
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            actual_phase = self.current_phase()
            if actual_phase == phase:
                LOG.debug(f'Election reached phase: {phase}.')
                return
            time.sleep(OGMIOS_POLL_SEC)
        raise TimeoutError(f'Election did not reach phase within {timeout}s: {phase}.')


    # TODO accept optional channel_id?
    def all_events(self) -> list[ChannelEvent]:
        # All events in _history, sorted by (slot_no, ch_str)
        events: dict[int, list[ChannelEvent]] = {}
        with self._history_lock:
            for (ch, es) in self._history.items():
                s = channel_id_to_string(ch)
                for e in es:
                    k = (e.slot_no, s)
                    if not k in events:
                        events[k] = []
                    events[k].append(e)
        events2 = []
        for k in sorted(list(events.keys())):
            events2 += events[k]
        return events2


    def all_election_events(self) -> list[ElectionEvent]:
        es = []
        for ch_evt in self.all_events():
            es += election_events(ch_evt)
        return es


    # TODO n_confirmations
    def is_confirmed(self, txid: str) -> bool:
        # Does _history contain this txid?
        events: list[ChannelEvent] = self.all_events()
        for e in events:
            if e.input_match and e.input_match['transaction_id'] == txid:
                return True
            if e.output_match and e.output_match['transaction_id'] == txid:
                return True
        return False


    # TODO wait_for_n_confirmations?
    def wait_for_confirmation(self, txid: str, timeout=OGMIOS_TIMEOUT_SEC):
        # Poll until _history contains txid
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_confirmed(txid):
                LOG.debug(f'txid {txid} confirmed in _history')
                return
            time.sleep(OGMIOS_POLL_SEC)
        raise TimeoutError(f'txid {txid} not confirmed in _history within {timeout}s.')


    def all_records(self) -> list[PublicRecord]:
        # All records in _history, sorted by slot_no
        records = []
        for e in self.all_events():
            # TODO just out states should cover it, right?
            if e.output_state:
                records += e.output_state.state.new_records
        return records


    # TODO why does this sometimes get stuck mid-election when refreshing?
    def version(self):
        "Re-use ETags for 204 no content checking in the webui"
        with self._history_lock:
            if not self._checkpoints:
                return 0
            return self._checkpoints[-1].header_hash


    def admin_address(self) -> Optional[Address]:
        log_call()
        try:
            with self._history_lock:
                event = self.channel_history(ADMIN_CHANNEL_ID)[-1]
                state = event.output_state if event.output_state else event.input_state
                vkh   = VerificationKeyHash(state.state.admin)
                addr  = Address(payment_part=vkh, network=Network.TESTNET) # TODO dynamic network
                return addr
        except Exception as e:
            LOG.error(e)
            return None


    ## process managment interface ##


    def start(self) -> None:
        # TODO assert being called from main thread?
        log_call()
        self._kupo_stop.clear()

        def _start_and_watch() -> None:
            LOG.debug('_start_and_watch')
            try:
                self._kupo_start()
                self._kupo_watch()
            except Exception as e:
                LOG.error(f'Error in watcher: {e}', exc_info=True)

        def handle_sigint(sig, frame):
            LOG.debug('_handle_sigint')
            LOG.debug(f'Signal {sig} recieved, shutting down...')
            self.stop()

        signal.signal(signal.SIGINT , handle_sigint)
        signal.signal(signal.SIGTERM, handle_sigint)

        self._kupo_thread = threading.Thread(
            target=_start_and_watch,
            daemon=False,
        )
        self._kupo_thread.start()


    def join(self):
        # TODO assert being called from main thread? or at least not the watcher
        log_call()
        t = self._kupo_thread
        if t and t is not threading.current_thread():
            t.join()
        LOG.debug(f'ElectionSubscriber stopped.')


    def request_stop(self):
        """Idempotent, safe to call from ANY thread (including the watcher)."""
        log_call()
        self._kupo_stop.set()
        if self._kupo_proc:
            self._kupo_proc.terminate()  # don't .wait() here; let watcher unwind


    def stop(self):
        """Full teardown + reap. Call only from a thread that is NOT the watcher."""
        log_call()
        self.request_stop()

        if self._kupo_proc:
            try:
                self._kupo_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._kupo_proc.kill()
                self._kupo_proc.wait()

        # TODO self.join here?
        t = self._kupo_thread
        if t and t is not threading.current_thread():
            LOG.debug('Waiting for watcher thread to exit...')
            t.join(timeout=5)
            if t.is_alive():
                LOG.warning('Watcher thread did not exit in time')
        self._kupo_thread = None


    def is_done(self):
        log_call()
        return self._kupo_stop.is_set() \
           and not self._kupo_thread.is_alive()


    def sleep(self, seconds):
        log_call()
        # This is kind of like time.sleep, except it short circuits properly during shutdown.
        self._kupo_stop.wait(timeout=seconds)


    ## process management ##


    def __del__(self):
        log_call()
        # Just a proactive warning in case of future thread stopping related issues:
        proc = getattr(self, '_kupo_proc', None)
        if proc is not None and proc.poll() is None:
            print(
                f'WARNING: ElectionSubscriber (kupo pid={proc.pid}) '
                f'was garbage-collected without stop() being called',
                file=sys.stderr,
            )
            try:
                proc.kill()
            except Exception:
                pass


    def _kupo_find_port(self):
        log_call()
        self._kupo_port = find_unused_port()
        LOG.debug(f'will start kupo on port {self._kupo_port}')


    def _kupo_start(self) -> None:
        '''
        Start Kupo as a subprocess.
        Uses `--since {slot}.{hash}` and `--match '{policy_id}/*'`.
        '''
        log_call()

        if self._kupo_proc is not None and self._kupo_proc.poll() is None:
            LOG.warning(f'Kupo already running (pid={self._kupo_proc.pid})')
            return

        since_arg = f'{self.election.deployment.since_slot}.{self.election.deployment.since_block}'

        cmd = [
            'kupo',
            '--ogmios-host', OGMIOS_HOST,
            '--ogmios-port', str(OGMIOS_PORT),
            '--in-memory',
            '--since', since_arg,
        ]

        # Start at the default 1442 and increment until one isn't in use.
        # TODO explicit port config and only use this as a fallback
        self._kupo_find_port()

        cmd += [
            '--match', f'{self.election.script.policy_id}/*',
            '--host', KUPO_HOST,
            '--port', str(self._kupo_port),
            '--log-level', 'Warning'
        ]

        LOG.debug(f'Starting Kupo: {' '.join(cmd)}')
        self._kupo_proc = subprocess.Popen(
            cmd,
            start_new_session=True, # Isolate child in its own process group so it doesn't get Ctrl-C directly
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Log Kupo output in a helper thread
        self._log_thread = threading.Thread(
            target=self._kupo_log,
            args=(),
            daemon=True,
        )
        self._log_thread.start()

        # prevents polling error during startup
        # TODO if this becomes a problem, wait for /health -> 200 OK instead
        # self.sleep(1)
        # time.sleep(OGMIOS_POLL_SEC + 1) # TODO how long is actually needed?


    def _kupo_log(self) -> None:
        log_call()
        proc = self._kupo_proc
        if proc.stdout is None:
            return
        for line in proc.stdout:
            line = line.rstrip('\n')
            if not line:
                continue
            LOG.debug(f'Kupo output: {line}')
            if proc.poll() is not None:
                break
        LOG.debug('Kupo subprocess output thread terminating')


    def _kupo_watch(self) -> None:
        log_call()
        LOG.debug(f'Watcher thread started for policy_id={self.election.script.policy_id}')
        while not self._kupo_stop.is_set():
            try:

                # This is split into fetch and handle matches to make it easier to test rollbacks.
                # (See test_subscriber.py for an example of that)
                # TODO is this lock needed? does it prevent refresh issues?
                with self._history_lock:
                    matches_by_sc = self._fetch_matches_by_sc()
                    self._handle_matches(matches_by_sc)

                self.sleep(KUPO_POLL_SEC)
            except requests.RequestException as e:
                LOG.warning(f'Kupo polling error: {e}') # TODO error?
            except KeyboardInterrupt:
                raise
            except Exception as e:
                LOG.error(f'Unexpected error in watcher: {e} {type(e)}', exc_info=True)
                raise
        LOG.debug('Watcher thread exiting')


    ## main event polling algorithm ##


    def _handle_matches(self, matches_by_sc):
        log_call()

        if not matches_by_sc:
            return

        # 1. Assemble matches into (input, output) pairs, still by (slot_no, channel_str).
        io_pairs_by_sc = self._pair_inputs_with_outputs(matches_by_sc)

        # 2. Add actions (AKA redeemers), still keyed by (slot_no, channel_str).
        ioa_triples_by_sc = self._fill_in_actions(io_pairs_by_sc)

        # 3. Assemble event objects, now with no need for keys.
        for event in self._assemble_events(ioa_triples_by_sc):

            if self._is_duplicate_event(event):
                # print(f'discard duplicate channelevent: {event}')
                continue

            if self._handle_same_but_spent(event):
                # print(f'discard same-but-spent channelevent: {event}')
                continue

            # 4. Update internal state and do some double checking + cleanup for
            #    particular action types.
            event = self._on_action(event)

            # 5. Emit final ElectionEvents to clients
            for event in election_events(event):
                self._on_election_event(event)


    def _kupo_api_url(self) -> str:
        log_call()
        return f'http://{KUPO_HOST}:{self._kupo_port}/v1'


    def _get_checkpoint(self, slot_no=None) -> Optional[Point]:
        # If not given a particular slot_no, uses the latest one.
        # TODO should it return a point if none exactly match slot_no?
        # TODO remove the slot_no option if not using it anymore?
        log_call()
        with self._history_lock:
            n_points = len(self._checkpoints)
            LOG.debug(f'Have {n_points} saved checkpoints.')
            if len(self._checkpoints) == 0:
                return None
            elif slot_no is None:
                return self._checkpoints[-1]
            else:
                return next(
                    (p for p in reversed(self._checkpoints) if p.slot_no == slot_no),
                    None
                )


    def _add_checkpoint(self, headers: dict) -> bool:
        # This returns whether a checkpoint was added, but that info isn't
        # currently used to decide anything.
        log_call()
        try:
            tip = Point.from_kupo_headers(headers)
        except KeyError:
            # Kupo doesn't seem to send these until the first match is found.
            LOG.debug(f"Wait for Kupo to send slot + block hash.")
            return False
        with self._history_lock:
            if len(self._checkpoints) > 0 and tip == self._checkpoints[-1]:
                return False
            else:
                self._checkpoints.append(tip)
                LOG.debug(f'Saved checkpoint {tip}')
                self._checkpoints = self._checkpoints[-KUPO_MAX_CHECKPOINTS:]
                return True


    def _fetch_matches_by_sc(self) -> list[dict]:
        log_call()
        base_params = {"order": "oldest_first"}

        # The tip Point should advance with the chain tip as reported by Kupo
        # in the previous fetch. That way we get 304 when nothing has changed.
        tip = self._get_checkpoint()
        headers = {"If-None-Match": tip.header_hash} if tip else {}

        if self._unpaired_matches:
            LOG.debug(f'Have {len(self._unpaired_matches)} unpaired matches to re-inject with the next batch.')

        r1_params = {}
        r1 = self._session.get(
            f"{self._kupo_api_url()}/matches",
            params={**base_params, **r1_params},
            headers=headers,
        )

        LOG.debug(f'r1 headers {r1.headers}')

        self._add_checkpoint(r1.headers)

        if r1.status_code == 400:
            # Kupo can't find the block header from the latest checkpoint anymore,
            # implying a rollback.
            return self._handle_rollback()

        if r1.status_code == 304:
            LOG.debug(f'Got 304 not modified.')
            return {}

        r1.raise_for_status()
        matches1 = r1.json()

        # There used to be a 2nd query r2 here. One was for created_after and
        # one for spent_after, and they both advanced with a shared
        # _matches_cursor Point. It sounds better in theory to avoid duplicate
        # events but there were always mysterious errors and issing matches.
        # Not sure if the algorithm was wrong or if Kupo doesn't actually
        # support alternating queries? Anyway one works, and it should NOT use
        # the created_after or spent_after params. Current algorithm expects
        # duplicate events and drops them instead.

        matches = matches1
        LOG.debug(f'n matches: {len(matches)}')
        if len(matches) == 0:
            return {}

        # Start from previous partial matches if any.
        # TODO clear them after they've been retried once or a couple times, if that comes up
        prev_matches = self._unpaired_matches
        self._unpaired_matches = []
        if prev_matches:
            LOG.debug(f'Re-injecting {len(prev_matches)} previous unpaired matches:\n{pformat(prev_matches)}')

        # Merge by (txid, output_index)
        # TODO no longer needed with just one query, or still a good structure?
        matches_by_sc = {}
        for m in prev_matches + matches:
            ch_str = kupo_match_to_channel_str(m)

            created_key = (m['created_at']['slot_no'], ch_str)
            matches_by_sc[created_key] = m

            if m['spent_at'] is not None:
                spent_key = (m['spent_at']['slot_no'], ch_str)
                matches_by_sc[spent_key] = m

        if matches_by_sc:
            LOG.debug(f'Processing {len(matches_by_sc)} merged matches:\n{pformat(matches_by_sc)}')

        return matches_by_sc


    def _pair_inputs_with_outputs(self, matches_by_sc: dict) -> list[Tuple[Optional[dict], Optional[dict]]]:
        log_call()

        io_pair_keys = sorted(list(matches_by_sc.keys()))
        if io_pair_keys:
            LOG.debug(f'io_pair_keys:\n{pformat(io_pair_keys)}')

        matches_flat = list(matches_by_sc.values())

        inputs_by_sc  = defaultdict(lambda: None)
        outputs_by_sc = defaultdict(lambda: None)

        # The iteration here is optimized for reading the logs, not efficiency.
        for key in io_pair_keys:
            LOG.debug(f'finding inputs and outputs of {key}')
            (slot_no, ch_str) = key

            for m in matches_flat:
                if kupo_match_to_channel_str(m) != ch_str:
                    continue
                is_input = m['spent_at'] and m['spent_at']['slot_no'] == slot_no
                if is_input:
                    LOG.debug(f'found input to {key}: {m}')
                    inputs_by_sc[key] = m
                    break

            for m in matches_flat:
                if kupo_match_to_channel_str(m) != ch_str:
                    continue
                is_output = m['created_at']['slot_no'] == slot_no
                if is_output:
                    LOG.debug(f'found output to {key}: {m}')
                    outputs_by_sc[key] = m
                    break

        LOG.debug(f'inputs_by_sc:\n{pformat(dict(inputs_by_sc))}')
        LOG.debug(f'outputs_by_sc:\n{pformat(dict(outputs_by_sc))}')

        io_pairs_by_sc = {
            k: (inputs_by_sc[k], outputs_by_sc[k])
            for k in io_pair_keys
        }

        if io_pairs_by_sc:
            LOG.debug(f'io_pairs_by_sc:\n{pformat(io_pairs_by_sc)}')
        return io_pairs_by_sc


    def _find_output_for_input(self, in_sc_key, matches_by_sc) -> Optional[dict]:
        log_call()
        (in_s, in_c) = in_sc_key
        in_match = matches_by_sc[in_sc_key]
        outputs = [
            m for ((s, c), m) in matches_by_sc.items()
            if s > in_s
            and c == in_c
            and m['transaction_id'] == in_match['spent_at']['transaction_id']
        ]
        assert len(outputs) < 2, f'More than 2 possible outputs found for {in_sc_key}'
        if len(outputs) == 1:
            return outputs[0]
        else:
            return None


    def _find_input_for_output(self, out_sc_key: dict, matches_by_sc: dict) -> Optional[dict]:
        log_call()
        (out_s, out_c) = out_sc_key
        out_match = matches_by_sc[out_sc_key]
        inputs = [
            m for ((s, c), m) in matches_by_sc.items()
            if s < out_s
            and c == out_c
            and m['spent_at']['transaction_id'] == out_match['transaction_id']
        ]
        assert len(inputs) < 2, f'More than 2 possible inputs found for {in_sc_key}'
        if len(inputs) == 1:
            return inputs[0]
        else:
            return None


    def _matches_to_search_for_actions(self, io_pairs_by_sc) -> list[dict]:
        log_call()
        # TODO search by txid + index, not just txid?
        # TODO make this more detailed so it's valid in general, not just when using identical redeemers
        matches_to_search = []
        for (input_match, output_match) in io_pairs_by_sc.values():
            matches_to_search += [input_match, output_match]
        for ch_id in self.current_channel_ids():
            with self._history_lock:
                prev_events = deepcopy(self._history[ch_id])
            for event in prev_events:
                matches_to_search += [event.input_match, event.output_match]
        matches_to_search = [m for m in matches_to_search if m is not None]
        return matches_to_search


    def _find_action(self, out_match: dict, matches_to_search: list[dict]) -> Optional[ElectionAction]:
        """Find the validator spend redeemer for a tx, ignoring mint redeemers."""
        log_call()
        txid = out_match['transaction_id']
        for m in matches_to_search:
            spent = m.get("spent_at")
            if spent and spent["transaction_id"] == txid:
                redeemer = spent["redeemer"]
                # TODO should this be part of decode_action?
                if not redeemer.startswith("d90500"):  # skip minting purpose tag
                    decoded = decode_action(redeemer)
                    return decoded
        return None


    def _fill_in_actions(self, io_pairs_by_sc):
        log_call()
        matches_to_search = self._matches_to_search_for_actions(io_pairs_by_sc)
        ioa_triples_by_sc = {}
        for (key, (in_match, out_match)) in io_pairs_by_sc.items():
            if in_match is not None:

                # TODO what does it mean when this is not a plutus constructor?
                # TODO is there a danger of mint redeemers when looking up directly too?
                try:
                    action = decode_action(in_match['spent_at']['redeemer'])
                except ValueError:
                    action = None

            else:
                assert out_match is not None, 'both in_match and out_match should not be None'
                from_prev = self._find_action(out_match, matches_to_search)
                if from_prev is not None:
                    # no input but can find redeemer in other matches = match on that to confirm: sub mint
                    action = from_prev
                else:

                    # This is (was) a common way for bugs to manifest. But the
                    # assertions to double check that InitElection is correct
                    # here turned out to cause more trouble than they
                    # prevented; checking further downstream in the algorithm
                    # is easier.
                    LOG.debug(f'InitElection with {key}\n{in_match}\n{out_match}\n')
                    action = InitElection()

            ioa_triple = (in_match, out_match, action)
            ioa_triples_by_sc[key] = ioa_triple

        if ioa_triples_by_sc:
            LOG.debug(f'ioa_triples_by_sc:\n{pformat(ioa_triples_by_sc)}')
        return ioa_triples_by_sc


    def _assemble_events(self, ioa_triples_by_sc: dict) -> Iterable[ChannelEvent]:
        log_call()

        for (key, val) in ioa_triples_by_sc.items():
            (slot_no, ch_str) = key
            (input_match, output_match, action) = val

            if self._handle_unpaired_match(ch_str, val):
                continue

            input_state  = self._fetch_state( input_match) if  input_match else None
            output_state = self._fetch_state(output_match) if output_match else None

            kwargs = {
                'slot_no'      : slot_no,
                'channel_id'   : coerce_channel_id(ch_str),
                'action'       : action,
                'input_match'  : input_match,
                'output_match' : output_match,
                'input_state'  : input_state,
                'output_state' : output_state,
            }

            # Because UTXOs often/usually first appear as unspent, then change to spent,
            # we exclude the output_match['spent_at'] part from the ID hash:
            # TODO factor out?
            kwargs_for_id = deepcopy(kwargs)
            if kwargs_for_id['output_match']:
                kwargs_for_id['output_match']['spent_at'] = None
            kwargs['id'] = f'channelevent-{unique_id(**kwargs_for_id)}'

            event = ChannelEvent(**kwargs)
            LOG.debug(f'event:\n{pformat(event)}')
            yield event


    def _fetch_state(self, kupo_match: dict) -> ChannelState:
        log_call()
        LOG.debug(f'kupo_match: {kupo_match}')
        datum_hash = kupo_match['datum_hash']
        url = self._kupo_api_url() + f'/datums/{datum_hash}'
        LOG.debug(f'fetching datum {datum_hash}')
        resp = self._session.get(url, timeout=10)
        resp.raise_for_status()
        datum = resp.json()
        LOG.debug(f'fetched {datum_hash} -> {datum}')
        state = decode_plutusdata_union(ChannelState, datum['datum'])
        LOG.debug(f'decoded {datum} -> {state}')
        return state


    ## handle polling issues ##


    def _handle_same_but_spent(self, event) -> bool:
        log_call()
        i = event.channel_id
        s = channel_id_to_string(i)
        with self._history_lock:
            if i in self._history and len(self._history[i]) > 0:
                prev_event = self._history[i][-1]
                # The 1st type of "same but spent" is that we get them in order and should update.
                # No point announcing the update externally though; that would be annoying.
                if _same_but_spent(prev_event, event):
                    self._history[i][-1] = event
                    LOG.debug(f'Replaced last {s} event with a new spent version.')
                    diff = safe_deepdiff(prev_event, event)
                    LOG.debug(f'diff before and after: {diff}')
                    return True
                 # The 2nd type is we get the spent one first, and should ignore the unspent.
                if _same_but_spent(event, prev_event):
                    LOG.debug(f'Ignored spent version of already-unspent {s} channel head.')
                    return True
            else:
                return False


    def _is_duplicate_event(self, event) -> bool:
        log_call()
        # TODO why are there sometimes duplicates of all events at once?
        i = event.channel_id
        with self._history_lock:
            if i in self._history:
                ch_str = channel_id_to_string(i)
                for (n, e) in enumerate(self._history[i]):
                    if e == event:
                        LOG.debug(f'Ignore duplicate of {ch_str} event {n}.')
                        return True
        return False


    def _handle_unpaired_match(self, ch_str, ioa_triple) -> bool:
        # Sometimes we get a match back from Kupo that doesn't seem to fit into
        # an input/output pair. Not sure whether that's a Kupo thing or a bug
        # in our matching algorithm. For now the cleanest fix seems to be to
        # stash those matches and re-inject them next poll.
        log_call()

        (input_match, output_match, action) = ioa_triple

        if input_match is None and not is_being_minted(ch_str, action):
            # LOG.debug(f'Dropping triple with missing input_match: {key} : {val}')
            LOG.debug(f'Saving unpaired output_match for later: {output_match}')
            self._unpaired_matches.append(output_match)
            return True

        if output_match is None and not is_being_burned(ch_str, action):
            # LOG.debug(f'Dropping triple with missing output_match: {key} : {val}')
            LOG.debug(f'Saving unpaired input_match for later: {input_match}')
            self._unpaired_matches.append(input_match)
            return True

        return False


    def _handle_rollback(self):
        log_call()

        # This is just the simplest probably-workable method for now.
        # For production use it should be cleaner and report a state diff to clients.
        # There should probably be a custom exception class too.
        # TODO write a test to call this manually and verify it works

        with self._history_lock:

            lost = self._checkpoints.pop()
            prev = self._get_checkpoint()
            LOG.warning(f'Rolling back {lost} -> {prev}')

            if prev is None:
                LOG.debug('No checkpoint to roll back to; dropping entire history.')
                self._history = {}

            else:
                LOG.debug(f'Dropping all events before slot {prev.slot_no}')
                ch_ids = sorted(list(self._history.keys()))
                for ch_id in ch_ids:
                    ch_str = channel_id_to_string(ch_id)
                    ch_events = self._history[ch_id]
                    while ch_events and ch_events[-1].slot_no >= prev.slot_no:
                        dropped = ch_events.pop()
                        LOG.debug(f'Rolling back {ch_str} event: {dropped}')
                    if len(ch_events) == 0:
                        del self._history[ch_id]

            LOG.debug('Clearing unpaired matches')
            self._unpaired_matches = []

        # 4. retry fetch, which may call this function again if needed
        return self._fetch_matches_by_sc()


    ## handle events ##


    def _on_action(self, event: ChannelEvent):
        log_call()
        LOG.debug(f'dispatching event:\n{pformat(event)}')
        match event.action:
            case InitElection():             return self._on_initelection(event)
            case AddSubChannels(channels):   return self._on_addsubchannels(event)
            case AdvancePhase():             return self._on_advancephase(event)
            case EndElection():              return self._on_endelection(event)
            case RmSubChannels(channels=_):  return self._on_rmsubchannels(event)
            case RebalanceFunds(channels=_): return self._on_rebalancefunds(event)
            case PostPublicRecords():        return self._on_postpublicrecords(event)
            case BurnTestTokens():           return self._on_burntesttokens(event)
            case _:                          raise NotImplementedError


    def _on_initelection(self, event: ChannelEvent):
        log_call()
        if self.current_phase() != 'ElectionNotStarted':
            i = event.channel_id
            with self._history_lock:
                prev = self._history[i][-1]
            diff = safe_deepdiff(prev, event)
            LOG.error(f'diff:\n{pformat(diff)}')
        assert self.current_phase() == 'ElectionNotStarted', 'InitElection should always happen first'
        assert event.channel_id == ADMIN_CHANNEL_ID # note this tx was published by the funder
        self._on_mint(event)
        return event


    def _on_addsubchannels(self, event: ChannelEvent):
        log_call()
        # remember this will be called once per channel touched
        if event.channel_id == ADMIN_CHANNEL_ID:
            self._on_cont(event)
        else:
            self._on_mint(event)
        return event


    def _on_advancephase(self, event: ChannelEvent):
        log_call()
        assert event.channel_id == ADMIN_CHANNEL_ID, 'only admin can advance phase'
        self._on_cont(event)
        return event


    def _on_endelection(self, event: ChannelEvent):
        # TODO is this a good place to self.stop()? or does that need to be done elsewhere?
        log_call()
        assert event.channel_id == ADMIN_CHANNEL_ID, 'only admin can end election'
        self._on_burn(event)
        self.request_stop()
        return event


    def _on_rmsubchannels(self, event: ChannelEvent):
        log_call()
        # remember this will be called once per channel touched
        assert event.channel_id in self._history, f'tried to remove non-existent channel {event.channel_id}'
        if event.channel_id == ADMIN_CHANNEL_ID:
            self._on_cont(event)
        else:
            self._on_burn(event)
        return event


    def _on_rebalancefunds(self, event: ChannelEvent):
        log_call()
        # remember this will be called once per channel touched
        self._on_cont(event)
        return event


    def _on_postpublicrecords(self, event: ChannelEvent):
        log_call()
        # TODO fetch from IPFS here
        self._on_cont(event)
        return event


    def _on_burntesttokens(self, event: ChannelEvent):
        log_call()
        # TODO remove for production use, or make a CLI flag for it
        self._on_burn(event)
        self.request_stop()
        return event


    def _on_mint(self, event: ChannelEvent):
        log_call()
        # LOG.debug(f'history during _on_mint:\n{pformat(self._history)}')
        with self._history_lock:
            assert not event.channel_id in self._history, f"tried to mint existing channel!\n{event}\n{self._history}"
            self._history[event.channel_id] = [event]
        out_seq = event.output_state.state.seq
        assert out_seq == 0, f'mint with non-0 seq {event}'


    def _on_burn(self, event: ChannelEvent):
        log_call()
        ch_str = channel_id_to_string(event.channel_id)
        assert event.output_state is None, f'{ch_str} being removed, but has an output'
        with self._history_lock:
            self._history[event.channel_id].append(event)


    def _on_cont(self, event: ChannelEvent):
        log_call()
        assert event.input_match  is not None, 'continuation without input_match'
        assert event.input_state  is not None, 'continuation without input_state'
        assert event.output_match is not None, 'continuation without output_match'
        assert event.output_state is not None, 'continuation without output_state'
        in_seq  = event.input_state.state.seq
        out_seq = event.output_state.state.seq
        assert in_seq + 1 == out_seq, f'state seq error: {in_seq} -> {out_seq} in {event}'
        with self._history_lock:
            assert event.channel_id in self._history, f'_on_cont but {event.channel_id} not in history'
            self._history[event.channel_id].append(event)
