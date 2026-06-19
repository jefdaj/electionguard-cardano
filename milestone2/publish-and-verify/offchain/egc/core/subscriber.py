import socket
import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
import logging
import itertools
from copy import copy
import random

from urllib.parse import urlencode
from dataclasses import dataclass, replace
from os import environ
from pprint import pformat
from collections import defaultdict
from deepdiff import DeepDiff

from typing import Any, Callable, Dict, List, Tuple, Optional, Self, Iterable

from .ogmios import *
from .plutus.types.channel import *
from .plutus.types.action import *
from .plutus.types.channel import *
from .election import ElectionContext

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LOG = logging.getLogger(__name__)

from pycardano import *

# TODO use https://pypi.org/project/kupo-py/ ?


# The port will be incremented if in use.
# TODO explicit config would be better
KUPO_HOST = environ.get('KUPO_HOST', '127.0.0.1')
KUPO_PORT = int(environ.get('KUPO_PORT', '1442'))


@dataclass
class SubscriberConfig:
    since_slot:       int # For kupo --since
    since_block_hash: str # For kupo --since
    policy_id:        str # For kupo --match

    # TODO remove?
    until_slot: Optional[int] = None # For kupo --until, to prevent open-ended scans during tests

    @classmethod
    def from_election(cls, election: ElectionContext) -> Self:
        return cls(
            election.deployment.index_from_slot,
            election.deployment.index_from_block_hash,
            str(election.script.policy_id), # TODO use the pycardano object?
            None,
        )


# TODO also use this in subscriberconfig?
@dataclass
class Point:
    slot_no: int
    header_hash: str

    def as_param(self) -> str:
        return f"{self.slot_no}.{self.header_hash}"

    @classmethod
    def from_config(cls, data: SubscriberConfig) -> Self:
        return cls(data.since_slot, data.since_block_hash)

    @classmethod
    def from_kupo_resp(cls, data: dict):
        return cls(data['slot_no'], data['header_hash'])


# These don't quite correspond to UTXOs because we store the state from the
# latest UTXO but the redeemer used to spend the previous UTXO on that channel.
# TODO is that overcomplicating it? maybe just store the redeemers as expected, or not at all?
# TODO rename? ChannelTransition etc. maybe later
# When a TX changes more than one channel, a ChannelEvent will be created for
# each one. For example: add or rm 3 channels -> 4 events.
@dataclass
class ChannelEvent:

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


# TODO move to channel_id.py
def channel_id_from_asset_name(encoded: str) -> ChannelId:
    channel_id = bytes.fromhex(encoded)
    # assert ChannelIdHelper.validate_bytes(channel_id)
    LOG.debug(f'decoded {asset_name} -> {channel_id}')
    return channel_id


# TODO remove in favor of getting channel_ids from states?
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

def is_port_in_use(port: int) -> bool:
    # based on https://stackoverflow.com/a/52872579
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((KUPO_HOST, port)) == 0


# TODO where should this live?
def kupo_match_to_channel_str(kupo_match: dict) -> str:
    asset_hex = list(kupo_match['value']['assets'].keys())[0].split('.')[-1]
    asset_str = bytes.fromhex(asset_hex).decode()
    channel_str = asset_str.split('-')[2]
    return channel_str


def kupo_match_to_pycardano_utxo(kupo_dict: dict) -> UTxO:
    """Convert a Kupo UTXO response dict to a PyCardano UTxO.
    WARNING: Does not handle a lot of edge cases! Mainly for BurnTestTokens.
    """
    LOG.debug('ElectionSubscriber.kupo_match_to_pycardano_utxo')
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


# TODO put in class
def find_spend_action(out_match: dict, matches: Iterable[dict]) -> Optional[ElectionAction]:
    """Find the validator spend redeemer for a tx, ignoring mint redeemers."""
    # TODO make this more detailed so it's valid in general, not just when using identical redeemers
    # LOG.debug(f'out_match: {out_match}')
    txid = out_match['transaction_id']
    for m in matches:
        spent = m.get("spent_at")
        if spent and spent["transaction_id"] == txid:
            redeemer = spent["redeemer"]
            if not redeemer.startswith("d90500"):  # skip minting purpose tag
                decoded = decode_action(redeemer)
                return decoded
    return None


def mk_example_callback(callback_name: str):
    def fn(event: ChannelEvent) -> None:
        print(f'\n{callback_name} called with:\n{pformat(event)}')
    return fn


def input_output_pairs(spent, unspent):

    def input_key(m):
        ch_str  = kupo_match_to_channel_str(m)
        slot_no = m['spent_at']['slot_no']
        # tx_id   = m['spent_at']['transaction_id']
        # return (slot_no, tx_id, ch_str)
        return (slot_no, ch_str)
        key_set.add(key)

    def output_key(m):
        ch_str  = kupo_match_to_channel_str(m)
        slot_no = m['created_at']['slot_no']
        # tx_id   = m['transaction_id']
        # return (slot_no, tx_id, ch_str)
        return (slot_no, ch_str)
        key_set.add(key)

    # find inputs + outputs for each key
    lists = defaultdict(lambda: ([], [])) # (inputs, outputs)
    for m in spent:
        k = input_key(m)
        lists[k][0].append(m)
    for m in spent + unspent:
        k = output_key(m)
        lists[k][1].append(m)
    LOG.debug(f'lists:\n{pformat(lists)}')

    # make sure there was only 0 or 1 of each, and simplify to pairs
    pairs_by_key = {}
    for (key, (inputs, outputs)) in lists.items():
        assert len(inputs) < 2
        assert len(outputs) < 2
        input_ = inputs[0]  if inputs  else None
        output = outputs[0] if outputs else None
        pairs_by_key[key] = (input_, output)
    LOG.debug(f'pairs_by_key:\n{pformat(pairs_by_key)}')

    return pairs_by_key


def _same_but_now_spent(old_event, new_event) -> bool:
    diff = DeepDiff(old_event, new_event)
    changes = diff.get("type_changes", {})
    try:
        assert set(diff.keys()) == {"type_changes"}, f"Unexpected diff keys: {diff.keys()}"
        assert len(changes) == 1, f"Expected 1 change, got: {changes}"
        change = changes.get("root.output_match['spent_at']")
        assert change is not None, "Expected spent_at to change"
        assert change["old_value"] is None
        assert isinstance(change["new_value"], dict)
        return True
    except:
        return False

# TODO where should this live?
def decode_action(redeemer_str):
    return decode_plutusdata_union(ElectionAction, redeemer_str)


def make_session():
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
    return s


class ElectionSubscriber:
    '''Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block_hash should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    '''

    def __init__(
            self,
            config: SubscriberConfig,
            on_action   = mk_example_callback('on_action'),
            on_rollback = mk_example_callback('on_rollback'),
        ):

        LOG.debug('ElectionSubscriber.__init__')

        self.config = config

        # High-level callbacks
        self.on_action   = on_action
        self.on_rollback = on_rollback

        # State is split into current and historical, because that makes it
        # simpler to work with Kupo's spent and unspent UTXO filters. When a
        # UTXO is spent we remove it from current and append its new spent
        # equivalent to history.
        # TODO write lock on self.history while mutating?
        self.history: Mapping[ChannelId, list[ChannelEvent]] = {}

        # for managing the kupo process
        self.kupo_proc:   Optional[subprocess.Popen] = None
        self.kupo_thread: Optional[threading.Thread] = None
        self.kupo_stop = threading.Event()

        # this will be updated when starting kupo to avoid conflicts with existing processes
        self.kupo_port = KUPO_PORT

        # for http requests to the kupo process
        self.session = make_session()
        self.session.headers.update({'Accept': 'application/json'})

        # Starting at the point from the config seems logical,
        # but for some reason Kupo rejects it. None works fine.
        # self.cursor = Point.from_config(self.config)
        self.cursor = None
        
        self.cursor3 = None
        self.etag = None

        # For debugging.
        # TODO remove
        self.prev_events = set()
        self.seen_matches = set()
        
        self.poll3_prev_events = set()


    ## query interface ##

    def all_channel_ids(self) -> list[ChannelId]:
        # Includes historical channels that have already been closed.
        LOG.debug('ElectionSubscriber.all_channel_ids')
        return sorted(list(self.history.keys()))

    def current_channel_ids(self) -> list[ChannelId]:
        LOG.debug('ElectionSubscriber.current_channel_ids')
        return [
            i for i in self.all_channel_ids()
            if self.current_state(i) is not None
        ]

    def channel_history(self, channel_id: ChannelId) -> list[ChannelEvent]:
        # Works fine on already-closed channels. Raises KeyError on not-yet-opened ones.
        LOG.debug('ElectionSubscriber.channel_history')
        return self.history[channel_id] # TODO return None rather than raise KeyError?

    def current_utxo(self, channel_id: ChannelId) -> Optional[UTxO]:
        # Returns None if the channel hasn't been opened yet or was already closed
        LOG.debug('ElectionSubscriber.current_utxo')
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
        LOG.debug('ElectionSubscriber.current_state')
        try:
            event = self.channel_history(channel_id)[-1]
        except KeyError:
            return None
        s = event.output_state # may also be None
        LOG.debug(f'Current state of {channel_id}: {s}')
        return s

    def current_phase(self) -> Optional[ElectionPhase]:
        # Returns None if the election hasn't started yet
        try:
            event = self.channel_history(ADMIN_CHANNEL_ID)[-1]
            return event.output_state.state.phase
        except KeyError:
            return None
 

    ## process managment interface ##

    def start(self) -> None:
        LOG.debug('ElectionSubscriber.start')
        self.kupo_stop.clear()

        def _start_and_watch() -> None:
            try:
                self._start_kupo()
                self._watch_kupo()
            except Exception as e:
                LOG.error(f'Error in watcher: {e}', exc_info=True)

        def handle_sigint(sig, frame):
            LOG.debug(f'Signal {sig} recieved, shutting down...')
            self.stop()

        signal.signal(signal.SIGINT , handle_sigint)
        signal.signal(signal.SIGTERM, handle_sigint)

        self.kupo_thread = threading.Thread(
            target=_start_and_watch,
            daemon=False,
        )
        self.kupo_thread.start()

    def join(self):
        LOG.debug('ElectionSubscriber.join')
        # TODO how is this actually supposed to be done?
        n = 0
        while not self.is_done():
            time.sleep(1)
            n += 1
        LOG.debug(f'ElectionSubscriber stopped after {n} seconds')

    def stop(self) -> None:
        LOG.debug('ElectionSubscriber.stop')
        self._stop_kupo()
        self.kupo_stop.set()
        if self.kupo_thread and self.kupo_thread.is_alive():
            LOG.debug('Waiting for watcher thread to exit...')
            try:
                self.kupo_thread.join(timeout=5)
            except Exception as e:
                if not 'cannot join current thread' in str(e):
                    raise
        self.kupo_thread = None

    def is_done(self):
        LOG.debug('ElectionSubscriber.is_done')
        return self.kupo_stop.is_set() \
           and self.kupo_thread is None


    ## process management ##

    def __del__(self):
        LOG.debug('ElectionSubscriber.__del__')
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

    # TODO remove in favor of explicit config later (maybe election.json?)
    def _ensure_unused_port(self):
        LOG.debug('ElectionSubscriber._ensure_unused_port')
        # prevent a list of nodes starting at exactly the same time
        time.sleep(random.randint(1, 1000) / 100)
        while is_port_in_use(self.kupo_port):
            LOG.debug(f'port {self.kupo_port} is in use')
            self.kupo_port += 1
        LOG.debug(f'will start kupo on port {self.kupo_port}')

    def _start_kupo(self) -> None:
        '''
        Start Kupo as a subprocess.
        Uses `--since {slot}.{hash}` and `--match '{policy_id}/*'`.
        '''
        LOG.debug('ElectionSubscriber._start_kupo')

        if self.kupo_proc is not None and self.kupo_proc.poll() is None:
            LOG.warning(f'Kupo already running (pid={self.kupo_proc.pid})')
            return

        # os.makedirs(KUPO_WORKDIR, exist_ok=True)
        since_arg = f'{self.config.since_slot}.{self.config.since_block_hash}'

        cmd = [

            'kupo',

            '--ogmios-host', OGMIOS_HOST,
            '--ogmios-port', str(OGMIOS_PORT),

            # at least for development, in memory should be fine
            # '--workdir', KUPO_WORKDIR,
            '--in-memory',

            '--since', since_arg,
        ]

        # TODO is kupo ignoring this?
        if self.config.until_slot is not None:
            cmd += ['--until', str(self.config.until_slot)]

        self._ensure_unused_port()

        cmd += [

            '--match', f'{self.config.policy_id}/*',

            '--host', KUPO_HOST,
            '--port', str(self.kupo_port),

            '--log-level', 'Warning'

            # '--prune-utxo',

            # TODO is any margin needed in this case?
            # '--safety-margin', '100',

        ]

        LOG.debug(f'Starting Kupo: {' '.join(cmd)}')
        self.kupo_proc = subprocess.Popen(
            cmd,
            preexec_fn=os.setsid, # makes handling signals more reliable
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Log Kupo output in a helper thread
        self._log_thread = threading.Thread(
            target=self._log_kupo_output,
            args=(),
            daemon=True,
        )
        self._log_thread.start()

        # TODO if this becomes a problem, wait for /health -> 200 OK instead
        time.sleep(1) # prevents polling error during startup
        # self._wait_for_kupo_ready()

    def _wait_for_kupo_ready(self, timeout: float = 60.0, interval: float = 0.5) -> str:
        """Block until Kupo has indexed past slot 0. Returns the initial cursor point."""
        # TODO the right way probably involves /health instead
        time.sleep(1) # give it a little time before even trying TODO less, like 0.1?
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                r = self.session.get(f"{self._kupo_api_url()}/matches", params={}, timeout=5)
                checkpoint = r.headers.get("X-Most-Recent-Checkpoint", "0")
                etag = r.headers.get("ETag", "")# .strip('"')
                if r.status_code == 200 and int(checkpoint) > 0 and etag:
                    return f"{checkpoint}.{etag}"
            except (KeyError, requests.RequestException):
                pass  # kupo not up yet
            time.sleep(interval)
        raise TimeoutError(f"Kupo not ready after {timeout}s")

    def _log_kupo_output(self) -> None:
        LOG.debug('ElectionSubscriber._log_kupo_output')
        proc = self.kupo_proc
        if proc.stdout is None:
            return
        for line in proc.stdout:
            line = line.rstrip('\n')
            if not line:
                continue
            LOG.debug(f'Kupo output: {line}')
            if proc.poll() is not None:
                break
        # TODO why does this seem to happen immediately?
        LOG.debug('Kupo subprocess output thread terminating')

    def _stop_kupo(self) -> None:
        LOG.debug('ElectionSubscriber._stop_kupo')

        proc = self.kupo_proc
        if proc is None:
            return
        if proc.poll() is None:
            LOG.debug(f'Terminating Kupo (pid={proc.pid})')
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                LOG.warning('Kupo did not exit in time, killing...')
                proc.kill()
                proc.wait() # TODO remove?

        # Pipe gets EOF when proc exits; reader thread will return.
        # Explicitly join it so it can't be mid-log at interpreter shutdown.
        if self._log_thread is not None:
            self._log_thread.join(timeout=2)
            if self._log_thread.is_alive():
                LOG.warning('Kupo log reader did not exit')
            self._log_thread = None

        self.kupo_proc = None

    def _watch_kupo(self) -> None:
        LOG.debug('ElectionSubscriber._watch_kupo')
        LOG.debug(f'Watcher thread started for policy_id={self.config.policy_id}')
        while not self.kupo_stop.is_set():
            try:

                # working_events = self._poll()
                # try:
                # poll3_events = self._poll3()
                    # events_diff = DeepDiff(working_events, poll3_events)
                    # LOG.debug(f'events_diff:\n\n{events_diff}\n')
                # except Exception as e:
                    # LOG.error(f'poll3 error: {e}', exc_info=True)

                self._poll4()

            except requests.RequestException as e:
                LOG.warning(f'Kupo polling error: {e}') # TODO error?
            except Exception as e:
                LOG.error(f'Unexpected error in watcher: {e} {type(e)}', exc_info=True)
                raise
            finally:
                time.sleep(OGMIOS_POLL_SEC)
        LOG.debug('Watcher thread exiting')


    ## polling and http queries ##

    def _kupo_api_url(self) -> str:
        LOG.debug('ElectionSubscriber._kupo_api_url')
        return f'http://{KUPO_HOST}:{self.kupo_port}/v1'


    ## polling attempt 1 + 2 ##

#     def _remove_duplicate_matches(self, matches):
#         deduped = []
#         for match in matches:
#             if str(match) in self.seen_matches:
#                 LOG.debug(f'remove duplicate match: {match}')
#             else:
#                 self.seen_matches.add(str(match))
#                 deduped.append(match)
#         return deduped
# 
#     def _poll(self):
#         # Spent UTXOs are better in general because they have more info:
#         # - spent_at of course, which isn't really used so far
#         # - also the spending redeemer (to detect burns, to add to next event)
# 
#         LOG.debug('ElectionSubscriber._poll')
#         params = {"order": "oldest_first"}
# 
#         # TODO are there any edge cases where order matters here?
#         # First instinct: spent is safer to start with, because then we
#         # probably can't get one that was spent but not created yet?
#         LOG.debug(f'fetching with cursor {self.cursor}')
#         spent   = self._fetch_spent()
#         unspent = self._fetch_unspent()
# 
#         if len(spent) == 0 and len(unspent) == 0:
#             return
# 
#         (spent, unspent) = self._update_cursor_and_truncate(spent, unspent)
# 
#         # TODO if this helps, debug the fetching
#         spent   = self._remove_duplicate_matches(spent)
#         unspent = self._remove_duplicate_matches(unspent)
# 
#         all_spent = self._add_prev_spent(spent)
#         pairs_by_key = input_output_pairs(all_spent, unspent) # TODO make a method?
# 
#         for event in self._channel_events(pairs_by_key, all_spent):
# 
#             # TODO is there a cleaner way to do this?
#             i = event.channel_id
#             if i in self.history and len(self.history[i]) > 0:
#                 prev_event = self.history[i][-1]
#                 if _same_but_now_spent(prev_event, event):
#                     s = channel_id_to_string(i)
#                     self.history[i][-1] = event
#                     LOG.debug(f'Replaced last {s} event with a new spent version.')
#                     continue
# 
#             # TODO less similar names?
#             self._on_action(event) # internal callback
#             self.on_action(event)  # external callback
# 
#     def _add_prev_spent(self, new_spent):
#         LOG.debug('ElectionSubscriber._add_prev_spent')
#         # have to bring back prev spent matches here too,
#         # because the relevant ones may be in a prev batch
#         # TODO is that also important for the input_output_pairs?
#         # TODO should only the latest (current) state's old inputs be needed?
#         prev_events = [x for sub in self.history.values() for x in sub]
#         # prev_events = [self.history[i][-1] for i in self.current_channel_ids()]
#         # events = [c[-1] for c in self.history.values()]
#         # old_spent = [e.input_match for e in old_events if e.input_match is not None]
#         prev_spent = [e.input_match for e in prev_events if e.input_match is not None]
#         prev_spent = [m for m in prev_spent if not m in new_spent] # TODO are these guaranteed to be disjoint already?
#         LOG.debug(f'prev_spent: {prev_spent}')
#         return sorted(prev_spent + new_spent, key=lambda m: m['created_at']['slot_no']) # TODO no need to sort, right?
#
#     def _fetch_spent(self):
#         LOG.debug('ElectionSubscriber._fetch_spent')
#         params = {"order": "oldest_first"}
#         # if self.cursor is not None:
#         #     params["spent_after"] = self.cursor.as_param()
#         url = self._kupo_api_url() + "/matches?" + urlencode(params) + "&spent"
#         LOG.debug(f'fetch spent url: {url}')
#         r = self.session.get(url)
#         if r.status_code == 400:
#             # Cursor point no longer on chain — rollback past our cursor
#             # TODO retry first? seems to happen transiently sometimes?
#             self._handle_rollback()
#             return
#         r.raise_for_status()
#         matches = r.json()
#         # if self.cursor is not None:
#             # kupo returns matches inclusive? we don't want the duplicates
#         #     matches = [m for m in matches if m['spent_at']['slot_no'] > self.cursor.slot_no]
#         LOG.debug(f'spent matches: {json.dumps(matches, indent=2)}')
#         return matches
# 
#     def _fetch_unspent(self):
#         LOG.debug('ElectionSubscriber._fetch_unspent')
#         params = {"order": "oldest_first"}
#         # if self.cursor is not None:
#         #     params["created_after"] = self.cursor.as_param()
#         url = self._kupo_api_url() + "/matches?" + urlencode(params) + "&unspent"
#         LOG.debug(f'fetch unspent url: {url}')
#         r = self.session.get(url)
#         if r.status_code == 400:
#             # Cursor point no longer on chain — rollback past our cursor
#             self._handle_rollback()
#             return
#         r.raise_for_status()
#         matches = r.json()
#         # if self.cursor is not None:
#             # kupo returns matches inclusive? we don't want the duplicates
#         #     matches = [m for m in matches if m['created_at']['slot_no'] > self.cursor.slot_no]
#         LOG.debug(f'unspent matches: {json.dumps(matches, indent=2)}')
#         return matches
# 
#     def _update_cursor_and_truncate(self, spent, unspent):
#         LOG.debug('ElectionSubscriber._update_cursor_and_truncate')
# 
#         # get the latest point from each list
#         last_spent   = None if not spent   else Point.from_kupo_resp(spent[-1]['spent_at'])
#         last_unspent = None if not unspent else Point.from_kupo_resp(unspent[-1]['created_at'])
#         LOG.debug(f'last_spent: {last_spent}')
#         LOG.debug(f'last_unspent: {last_unspent}')
# 
#         # if they both have a last one, use the earlier
#         # TODO is this necessary? not sure if they're guaranteed to be the same
#         points = [p for p in (last_spent, last_unspent) if p is not None]
#         earlier = min(points, key=lambda p: p.slot_no)
#         LOG.debug(f'earlier: {earlier}')
# 
#         # cut off utxos after that from both lists (only one will have any),
#         # so they can be processed next poll loop without duplicate events
#         LOG.debug(f'lengths before truncation: spent={len(spent)}, unspent={len(unspent)}')
#         spent   = [m for m in spent   if m['spent_at'  ]['slot_no'] <= earlier.slot_no]
#         unspent = [m for m in unspent if m['created_at']['slot_no'] <= earlier.slot_no]
#         LOG.debug(f'lengths after truncation: spent={len(spent)}, unspent={len(unspent)}')
# 
#         # update cursor to the earlier so that the cut-off values will be
#         # fetched again next poll
#         self.cursor = earlier
#         LOG.debug(f'updated cursor to {earlier}')
# 
#         return (spent, unspent)
# 
#     def _fetch_datum(self, datum_hash: str) -> Any:
#         LOG.debug('ElectionSubscriber._fetch_datum')
#         # TODO adjust to port changes
#         url = self._kupo_api_url() + f'/datums/{datum_hash}'
#         LOG.debug(f'fetching datum {datum_hash}')
#         resp = self.session.get(url, timeout=10)
#         resp.raise_for_status()
#         return resp.json()
#
# def find_redeemer(kupo_match, spent_matches) -> Optional[ElectionAction]:
#     "Search spent_matches for a `spent_at` matching the current match."
#     tx_id = kupo_match.get('transaction_id')
#     for m in spent_matches:
#         spent = m.get('spent_at')
#         if spent['transaction_id'] == tx_id: # and spent['input_index'] == tx_ix:
#             LOG.debug(f'matching spent json: {spent}')
#             cbor = spent['redeemer']
#             redeemer = decode_plutusdata_union(ElectionAction, cbor)
#             LOG.debug(f'matching redeemer: {redeemer}')
#             return redeemer
#     LOG.debug(f'No matching redeemer for: {kupo_match}')
#     return None
#
#     def _channel_events(self, pairs_by_key, spent) -> Iterable[ChannelEvent]:
#         LOG.debug('channel_events')
#         # events = []
#         keys = sorted(pairs_by_key.keys())
#         first_event = True
#         for key in keys:
#             LOG.debug(f'key: {key}')
# 
#             (slot_no, channel_str) = key
#             LOG.debug(f'slot_no: {slot_no}')
#             LOG.debug(f'channel_str: {channel_str}')
# 
#             (input_match, output_match) = pairs_by_key[key]
#             LOG.debug(f'input_match: {input_match}')
#             LOG.debug(f'output_match: {output_match}')
# 
#             assert input_match is not None or output_match is not None, 'input and output matches cannot both be None'
# 
#             # Get states (AKA datums)
#             if input_match is not None:
#                 input_datum = self._fetch_datum(input_match['datum_hash'])['datum']
#                 input_state = decode_plutusdata_union(ChannelState, input_datum)
#             else:
#                 input_state = None
#             if output_match is not None:
#                 output_datum = self._fetch_datum(output_match['datum_hash'])['datum']
#                 output_state = decode_plutusdata_union(ChannelState, output_datum)
#             else:
#                 output_state = None
# 
#             # Get action (AKA redeemer)
#             if output_match is not None:
#                 if input_match is None:
#                     all_spent = spent
#                 else:
#                     all_spent = spent + [input_match]
#                 action = find_redeemer(output_match, all_spent)
#                 LOG.debug(f'action: {action}')
#                 if action is None:
#                     # Should only happen in the very first event, because the input
#                     # (the one-shot UTXO) doesn't have an STT and so doesn't match the
#                     # Kupo filter.
#                     assert channel_str == 'admin'
#                     assert input_state is None
#                     assert isinstance(output_state.state, AdminChannelState)
#                     assert output_state.state.seq == 0, f'output_state seq != 0: {output_state}'
#                     action = InitElection()
#                 assert action is not None
#             else:
#                 # TODO should this ever happen
#                 # TODO and why is the string interpolation working weirdly
#                 LOG.warning('no output_match, so no action can be found')
#                 action = None
# 
#             event = ChannelEvent(
#                 slot_no      = slot_no,
#                 channel_id   = coerce_channel_id(channel_str),
#                 action       = action,
#                 input_match  = input_match,
#                 output_match = output_match,
#                 input_state  = input_state,
#                 output_state = output_state,
#             )
#             LOG.debug(f'event:\n{pformat(event)}')
# 
#             if str(event) in self.prev_events:
#                 LOG.warning(f'duplicate event: {event}') # TODO debug
#             else:
#                 self.prev_events.add(str(event))
#                 yield event
#                 # events.append(event)
#         # return events


    ## polling attempt 3 ##

#    def _poll3_pairs_by_key(pairs: list[tuple]) -> dict:
#     """Transform _poll3_pair() output to (slot_no, channel_str) keyed dict."""
#     # TODO not really pairs; rename if using
#     pairs_by_key = {}
#     for (input_match, output_match, redeemer) in pairs:
#         if input_match is not None:
#             ch_str = kupo_match_to_channel_str(input_match)
#             slot_no = input_match["spent_at"]["slot_no"]
#         else:
#             # mint: no input, key by output's created_at
#             # TODO anything special needed for burns here?
#             ch_str = kupo_match_to_channel_str(output_match)
#             slot_no = output_match["created_at"]["slot_no"]
#         key = (slot_no, ch_str)
#         pair = (input_match, output_match, redeemer)
#         LOG.debug(f'poll3 pair by key: {key}: {pair}')
#         pairs_by_key[key] = pair
# 
#     LOG.debug(f'poll3 pairs_by_key:\n{pformat(pairs_by_key)}')
#     return pairs_by_key
#
#     def _poll3(self) -> list[tuple]:
#         base_params = {"order": "oldest_first"} #, "resolve_hashes": ""} TODO fix this to avoid 400
#         
#         # TODO merge cursor + etag into the same thing to be sure they change together
#         headers = {"If-None-Match": f'"{self.etag}"'} if self.etag else {}
# 
#         r1_params = {} if self.cursor3 is None else {"created_after": self.cursor3}
#         r2_params = {} if self.cursor3 is None else {"spent_after":   self.cursor3}
#         
#         # LOG.debug(f"poll3 sending etag={self.etag!r}, cursor={self.cursor!r}")
#         
#         # Q1: new outputs since cursor
#         r1 = self.session.get(
#             f"{self._kupo_api_url()}/matches",
#             params={**base_params, **r1_params},
#             headers=headers,
#         )
#         
#         # LOG.debug(f"poll3 r1 status={r1.status_code}, cp={r1.headers.get('X-Most-Recent-Checkpoint')}, etag={r1.headers.get('ETag')!r}")
# 
#         if r1.status_code == 304:
#             return []  # chain hasn't advanced
# 
#         if r1.status_code == 400:
#             raise NotImplementedError("Rollback detected (created_after)")
# 
#         r1.raise_for_status()
#         # LOG.debug(f'poll3 r1 headers {r1.headers}')
# 
#         # Q2: old inputs now spent since cursor
#         r2 = self.session.get(
#             f"{self._kupo_api_url()}/matches",
#             params={**base_params, **r2_params},
#             headers=headers, # TODO did claude forget this? or should it not be there?
#         )
# 
#         if r2.status_code == 400:
#             raise NotImplementedError("Rollback detected (spent_after)")
# 
#         r2.raise_for_status()
#         # LOG.debug(f'poll3 r2 headers {r2.headers}')
# 
#         # Verify both queries see the same chain tip
#         cp1 = r1.headers["X-Most-Recent-Checkpoint"]
#         cp2 = r2.headers["X-Most-Recent-Checkpoint"]
#         if cp1 != cp2:
#             return []  # retry next tick
# 
#         # Advance cursor
#         block_hash = r1.headers["ETag"].strip('"')
#         new_cursor = f"{cp1}.{block_hash}"
#         new_etag = r1.headers["ETag"].strip('"')
# 
#         # Merge by (txid, output_index), Q1 and Q2 may overlap
#         matches = {}
#         for m in r1.json() + r2.json():
#             key = (m["transaction_id"], m["output_index"])
#             matches[key] = m
# 
#         LOG.debug(f'matches:\n{pformat(matches)}')
#       
#         if new_cursor == self.cursor3 and new_etag == self.etag:
#             LOG.debug(f"poll3 chain hasn't advanced, but no 304? Throwing away {len(matches)} matches.")
#             return []
#             # LOG.debug(f"poll3 chain hasn't advanced, but no 304? Processing {len(matches)} matches anyway.")
#         else:
#             self.cursor3 = new_cursor
#             self.etag = new_etag
#             LOG.debug(f'poll3 advance cursor, etag to {self.cursor3}, {self.etag}. Processing {len(matches)} matches.')
# 
#         # TODO replace _poll3_pair, _poll3_pairs_by_key, _poll3_channel_events with one fn?
#         pairs = self._poll3_pair(matches)
#         pairs_by_key = _poll3_pairs_by_key(pairs)
# 
#         # TODO is this the best point to sort?
#         pairs_by_key = dict(sorted(pairs_by_key.items()))
#         
#         for event in self._poll3_channel_events(pairs_by_key):
# 
#             # TODO is there a cleaner way to do this?
#             i = event.channel_id
#             if i in self.history and len(self.history[i]) > 0:
#                 prev_event = self.history[i][-1]
#                 if _same_but_now_spent(prev_event, event):
#                     s = channel_id_to_string(i)
#                     self.history[i][-1] = event
#                     LOG.debug(f'Replaced last {s} event with a new spent version.')
#                     continue
# 
#             LOG.debug(f'poll3 event:\n{pformat(event)}')
# 
#             # TODO less similar names?
# 
#             # Internal callback does some per-action checks, updates history,
#             # and cleans up the event.
#             event_clean = self._on_action(event)
# 
#             # Then the last step is to hand the cleaned up event to the
#             # external callback.
#             self.on_action(event_clean)
# 
#     def _poll3_pair(self, matches: dict) -> list[tuple]:
# 
#         # TODO can you just do the entire dispatch thing in one function here??
# 
 
#         by_creating_tx = {}
#         for m in matches.values():
#             key = (m["transaction_id"], kupo_match_to_channel_str(m))
#             by_creating_tx[key] = m
#         LOG.debug(f'by_creating_tx:\n{pformat(by_creating_tx)}')
# 
#         # spending_txids = {
#             # m["spent_at"]["transaction_id"]
#             # for m in matches.values()
#             # if m["spent_at"]
#         # }
# 
#         # build set of txids that are outputs OF a spend we know about
#         has_known_input = {
#             m["spent_at"]["transaction_id"]
#             for m in matches.values()
#             if m["spent_at"]
#         }
#         LOG.debug(f'has_known_input:\n{pformat(has_known_input)}')
# 
#         events = []
# 
#         for m in matches.values():
#             action = find_spend_action(m['transaction_id'], matches)
# 
#             if m["transaction_id"] not in has_known_input:
#                 # this match has no known input = mint
#                 if m["spent_at"] is None:
#                     events.append((None, m, action))  # unspent mint head (TODO it should tho?)
#                 else:
#                     # spent mint — still emit as mint, paired with its output
#                     spending_txid = m["spent_at"]["transaction_id"]
#                     channel_str = kupo_match_to_channel_str(m)
#                     output = by_creating_tx.get((spending_txid, channel_str))
#                     events.append((None, m, action))  # mint, no redeemer (TODO it should tho?)
#             else:
#                 if m["spent_at"] is None:
#                     continue  # unspent continuation, not an event yet
#                 spending_txid = m["spent_at"]["transaction_id"]
#                 channel_str = kupo_match_to_channel_str(m)
#                 output = by_creating_tx.get((spending_txid, channel_str))
#                 events.append((m, output, action))
# 
# 
# # TODO totally wrong, right?
# #                 # emit as mint
# #                 events.append((None, m, action))
# #                 # fall through — if it's also spent, emit the continuation too
# # 
# #             if m["spent_at"] is None:
# #                 continue  # unspent head, no continuation yet
# # 
# #             spending_txid = m["spent_at"]["transaction_id"]
# #             asset = stt_asset(m)
# #             output = by_creating_tx.get((spending_txid, asset))
# #             # action = find_spend_action(spending_txid, matches)
# #             events.append((m, output, action))
# 
#         # missing_inputs = [
#         #     m for m in matches.values()
#         #     if m['spent_at'] is not None
#         #     and not m in [e[1] for e in events]
#         # ]
#         # if missing_inputs:
#         #     LOG.error(f'missing_inputs:\n{pformat(missing_inputs)}')
# 
#         # missing_outputs = [
#         #     m for m in matches.values()
#         #     if m['spent_at'] is None
#         #     and not m in [e[1] for e in events]
#         # ]
#         # if missing_outputs:
#         #     LOG.error(f'missing_outputs:\n{pformat(missing_outputs)}')
# 
#         
# 
#         # events.sort(key=lambda e: (
#         #     e[0]["spent_at"]["slot_no"] if e[0] and e[0]["spent_at"]
#         #     else e[1]["created_at"]["slot_no"]
#         # ))
#         return events
# 
#     def _poll3_channel_events(self, pairs_by_key) -> Iterable[ChannelEvent]:
#         # WARNING: these "pairs" are actually 3-tuples; will rename if works
#         LOG.debug('_poll3_channel_events')
#         # events = []
#         # keys = sorted(pairs_by_key.keys())
#         # for key in keys:
# 
#         # TODO no need to sort here right?
#         for key in sorted(pairs_by_key.keys()):
# 
#             LOG.debug(f'poll3 key: {key}')
# 
#             (slot_no, channel_str) = key
#             LOG.debug(f'poll3 slot_no: {slot_no}')
#             LOG.debug(f'poll3 channel_str: {channel_str}')
# 
#             pair = pairs_by_key[key]
#             (input_match, output_match, action) = pair
#             LOG.debug(f'poll3 input_match: {input_match}')
#             LOG.debug(f'poll3 output_match: {output_match}')
#             LOG.debug(f'poll3 action: {action}')
# 
# #             if redeemer_hex is None:
# #                 if input_match is None:
# #                     # Probably InitElection! Double check...
# #                     assert channel_str == channel_id_to_string(ADMIN_CHANNEL_ID)
# #                     # TODO assert output seq is 0
# #                     # TODO assert history is empty
# #                     action = InitElection()
# #                     LOG.debug(f'poll3 Special InitElection case: {pair}')
# #                 else:
# #                     # TODO what would this be?
# #                     action = None
# #                     LOG.warning(f'poll3 Failed to find action: {pair}')
# #             else:
# #                 action = decode_plutusdata_union(ElectionAction, redeemer_hex)
# #                 LOG.debug(f'poll3 action: {action}')
# 
#             assert input_match is not None or output_match is not None, 'input and output matches cannot both be None'
# 
#             # Get states (AKA datums)
#             # TODO this can be made inline later, right? but save until 304 works
#             if input_match is not None:
#                 input_datum = self._fetch_datum(input_match['datum_hash'])['datum']
#                 input_state = decode_plutusdata_union(ChannelState, input_datum)
#             else:
#                 input_state = None
#             if output_match is not None:
#                 output_datum = self._fetch_datum(output_match['datum_hash'])['datum']
#                 output_state = decode_plutusdata_union(ChannelState, output_datum)
#             else:
#                 output_state = None
# 
#             event = ChannelEvent(
#                 slot_no      = slot_no,
#                 channel_id   = coerce_channel_id(channel_str),
#                 action       = action,
#                 input_match  = input_match,
#                 output_match = output_match,
#                 input_state  = input_state,
#                 output_state = output_state,
#             )
# 
#             if str(event) in self.poll3_prev_events:
#                 LOG.warning(f'poll3 throwing away duplicate event: {event}') # TODO debug
#             else:
#                 self.poll3_prev_events.add(str(event))
#                 yield event
#                 # events.append(event)
#         # return events

    ## polling attempt 4 ##

    def _poll4(self):

        # Fetch matches, keyed by (slot_no, channel_str).
        matches_by_sc = self._poll4_fetch_matches()
        if not matches_by_sc:
            return

        # Assemble matches them into (input, output) pairs, still by (slot_no, channel_str).
        io_pairs_by_sc = self._poll4_input_output_pairs(matches_by_sc)

        # Add actions (AKA redeemers), still keyed by (slot_no, channel_str).
        # TODO test whether this is just bad with BurnTestTokens, or if something needs fixing
        ioa_triples_by_sc = self._poll4_add_actions(io_pairs_by_sc)

        # Assemble event objects, now with no need for keys.
        # These aren't quite ready to emit yet because they haven't been double checked.
        # events = self._poll4_assemble_events(ioa_triples_by_sc)

        # Update internal state (branching on action type) and emit finished events.
        # for event in events:
        for event in self._poll4_assemble_events(ioa_triples_by_sc):
            if self._poll4_handle_same_but_spent(event):
                continue
            if self._poll4_discard_duplicate(event):
                continue
            finished_event = self._on_action(event) # internal callback
            self.on_action(finished_event)          # external callback

    def _poll4_handle_same_but_spent(self, event) -> bool:
        # TODO is there a simpler way?
        i = event.channel_id
        s = channel_id_to_string(i)
        if i in self.history and len(self.history[i]) > 0:
            prev_event = self.history[i][-1]

            # The 1st type of "same but spent" is that we get them in order and should update.
            if _same_but_now_spent(prev_event, event):
                self.history[i][-1] = event
                LOG.debug(f'Replaced last {s} event with a new spent version.')
                return True

             # The 2nd type is we get the spent one first, and should ignore.   
            if _same_but_now_spent(event, prev_event):
                LOG.debug(f'Ignored spent version of already-unspent {s} channel head.')
                return True

        else:
            return False

    def _poll4_discard_duplicate(self, event) -> bool:
        i = event.channel_id
        if i in self.history:
            if event in self.history[i]:
                LOG.debug(f'Discard duplicate event: {event}')
                return True
        return False

    def _fetch_state(self, kupo_match: dict) -> ChannelState:
        LOG.debug('ElectionSubscriber._fetch_state')
        LOG.debug(f'kupo_match: {kupo_match}')
        datum_hash = kupo_match['datum_hash']
        url = self._kupo_api_url() + f'/datums/{datum_hash}'
        LOG.debug(f'fetching datum {datum_hash}')
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        datum = resp.json()
        LOG.debug(f'fetched {datum_hash} -> {datum}')
        state = decode_plutusdata_union(ChannelState, datum['datum'])
        LOG.debug(f'decoded {datum} -> {state}')
        return state

    def _poll4_assemble_events(self, ioa_triples_by_sc: dict) -> Iterable[ChannelEvent]:
        # events = []
        for ((slot_no, ch_str), (input_match, output_match, action)) in ioa_triples_by_sc.items():
            input_state  = self._fetch_state( input_match) if  input_match else None
            output_state = self._fetch_state(output_match) if output_match else None
            event = ChannelEvent(
                slot_no      = slot_no,
                channel_id   = coerce_channel_id(ch_str),
                action       = action,
                input_match  = input_match,
                output_match = output_match,
                input_state  = input_state,
                output_state = output_state,
            )
            LOG.debug(f'event:\n{pformat(event)}')
            yield event
            # events.append(event)
        # if events:
        #     LOG.debug(f'events:\n{pformat(events)}')
        # return events

    def _poll4_find_output_for_input(self, in_sc_key, matches_by_sc) -> Optional[dict]:
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

    def _poll4_find_input_for_output(self, out_sc_key: dict, matches_by_sc: dict) -> Optional[dict]:
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

    def _poll4_input_output_pairs(self, matches_by_sc: dict) -> list[Tuple[Optional[dict], Optional[dict]]]:

        io_pair_keys = sorted(list(matches_by_sc.keys()))
        if io_pair_keys:
            LOG.debug(f'io_pair_keys:\n{pformat(io_pair_keys)}')

        # These are the TXIDs we're currently determining input or output relative to.
        current_txids_by_slot = {
            # s : m["spent_at"]["transaction_id"]
            # for ((s, _), m) in matches_by_sc.items()
            # if m["spent_at"]
            s : m["transaction_id"]
            for ((s, _), m) in matches_by_sc.items()
        }

        inputs_by_sct = {}
        outputs_by_sct = {}
        for key in io_pair_keys:
            (tx_slot_no, ch_str) = key
            m = matches_by_sc[key]
            # created_tc_pair = (m['transaction_id'], ch_str)
            LOG.debug(f'classifying match {key}')
            # is_output = m['created_at']['slot_no'] == tx_slot_no

#             is_input = m['spent_at'] and m['spent_at']['slot_no'] == tx_slot_no
#             if is_input:
#                 txid = m['spent_at']['transaction_id']
#                 sct = (tx_slot_no, ch_str, txid)
#                 inputs_by_sct[sct] = m
#             else:
#                 txid = m['transaction_id']
#                 sct = (tx_slot_no, ch_str, txid)
#                 outputs_by_sct[sct] = m

            for (spending_slot_no, spending_txid) in current_txids_by_slot.items():
                if tx_slot_no != spending_slot_no:
                    continue

                match_is_input = m['spent_at'] and \
                                 m['spent_at']['transaction_id'] == spending_txid
                                 # m['spent_at']['slot_no'] == spending_slot_no and \
                if match_is_input:
                    LOG.debug(f'match {key} is an input to {spending_txid}')
                    sct = (spending_slot_no, ch_str, spending_txid)
                    inputs_by_sct[sct] = m

                match_is_output = m['created_at']['slot_no'] == spending_slot_no and \
                                  m['transaction_id'] == spending_txid
                if match_is_output:
                    LOG.debug(f'match {key} is an output of {spending_txid}')
                    sct = (spending_slot_no, ch_str, spending_txid)
                    outputs_by_sct[sct] = m

        LOG.debug(f'inputs_by_sct:\n{pformat(inputs_by_sct)}')
        LOG.debug(f'outputs_by_sct:\n{pformat(outputs_by_sct)}')

        # We only want to deal with inputs whose corresponding output isn't also in the match set.
        # These should be burns.
        out_keys = outputs_by_sct.keys()
        inputs_by_sct_deduped = {
            (s,c,t) : m
            for ((s,c,t), m) in inputs_by_sct.items()
            if  not (m['spent_at'  ]['slot_no'], c, t) in out_keys
            and not (m['created_at']['slot_no'], c, t) in out_keys
        }
        LOG.debug(f'inputs_by_sct_deduped:\n{pformat(inputs_by_sct_deduped)}')

        io_pairs_by_sc = {}

        for ((s,c,t), in_match) in inputs_by_sct_deduped.items():
            sc = (s,c)
            out_match = self._poll4_find_output_for_input(sc, matches_by_sc)
            pair = (in_match, out_match)
            io_pairs_by_sc[sc] = pair

        for ((s,c,t), out_match) in outputs_by_sct.items():
            sc = (s,c)
            in_match = self._poll4_find_input_for_output(sc, matches_by_sc)
            pair = (in_match, out_match)
            io_pairs_by_sc[sc] = pair

        # Re sort to make sure events are processed in chain order.
        io_pairs_by_sc = {
            k : io_pairs_by_sc[k]
            for k in sorted(io_pairs_by_sc.keys())
        }

#         created_tc_pairs = set(
#             (m["transaction_id"], c)
#             for ((s, c), m) in matches_by_sc.items()
#             if m['created_at']['slot_no'] == s
#         )
#         spent_tc_pairs = set(
#             (m["spent_at"]["transaction_id"], c)
#             for ((s, c), m) in matches_by_sc.items()
#             if m["spent_at"]
#             and m['created_at']['slot_no'] == s
#             # and m['spent_at']['slot_no'] == s
#         )
#         mint_tc_pairs = created_tc_pairs - spent_tc_pairs # TODO useful for InitElection?
#         burn_tc_pairs = spent_tc_pairs - created_tc_pairs
#         if mint_tc_pairs:
#             LOG.debug(f'mint_tc_pairs: {mint_tc_pairs}')
#         if burn_tc_pairs:
#             LOG.debug(f'burn_tc_pairs: {burn_tc_pairs}')
# 
#         io_pairs_by_sc = {}
#         for key in io_pair_keys:
#             (slot_no, ch_str) = key
#             match = matches_by_sc[key]
#             created_tc_pair = (match['transaction_id'], ch_str)
#             LOG.debug(f'classifying match {key}')
#             is_output = match['created_at']['slot_no'] == slot_no
#             if is_output:
#                 output = match
#                 LOG.debug(f'match {key} is an output')
#                 is_mint = created_tc_pair in mint_tc_pairs
#                 # if is_mint:
#                 #     LOG.debug(f'match {key} is a mint')
#                 #     input_ = None
#                 # else:
#                 LOG.debug(f'match {key} is not a mint; looking for input')
#                 input_ = self._poll4_find_input_for_output(key, matches_by_sc)
#             else:
#                 input_ = match
#                 LOG.debug(f'match {key} is an input')
#                 spent_tc_pair = (match['spent_at']['transaction_id'], ch_str)
#                 is_burn = spent_tc_pair in burn_tc_pairs
#                 # if is_burn:
#                 #     LOG.debug(f'match {key} is a burn')
#                 #     output = None
#                 # else:
#                 LOG.debug(f'match {key} is not a burn; looking for output')
#                 output = self._poll4_find_output_for_input(key, matches_by_sc)
#             pair = (input_, output)
#             io_pairs_by_sc[key] = pair

        if io_pairs_by_sc:
            LOG.debug(f'io_pairs_by_sc:\n{pformat(io_pairs_by_sc)}')
        return io_pairs_by_sc

    def _poll4_matches_to_search(self, current_matches: list[dict]) -> list[dict]:
        # TODO which of these are really necessary?
        # TODO search by txid + index, not just txid?
        matches_to_search = current_matches
        for ch_id in self.current_channel_ids():
            prev_events = self.history[ch_id]
            for event in prev_events:
                matches_to_search += [event.input_match, event.output_match]
        matches_to_search = [m for m in matches_to_search if m is not None]
        return matches_to_search

    def _poll4_add_actions(self, io_pairs_by_sc):
        ioa_triples_by_sc = {}
        prev_inputs = []
        current_matches = []
        for (i, o) in io_pairs_by_sc.values():
            current_matches += [i, o]
        matches_to_search = self._poll4_matches_to_search(current_matches)
        for (key, (in_match, out_match)) in io_pairs_by_sc.items():
            if in_match is not None:
                # has input = can find redeemer and match on that: continuation, sub burn, endelection
                # if in_match['spent_at'] is None:
                #     # TODO what to call this case?
                #     action = find_spend_action(in_match, io_pairs_by_sc.values())
                # else:
                # TODO is there a danger of mint redeemers when looking up directly too?
                action = decode_action(in_match['spent_at']['redeemer'])
            else:
                assert out_match is not None, 'both in_match and out_match should not be None'
                from_prev = find_spend_action(out_match, matches_to_search) # TODO expand search? # TODO expand search?
                if from_prev is not None:
                    # no input but can find redeemer in other matches = match on that to confirm: sub mint
                    action = from_prev
                else:
                    # no input, can't find redeemer, very first match, admin channel = initelection
                    LOG.debug(f'InitElection with {key}\n{in_match}\n{out_match}\n')
                    # assert key[1] == channel_id_to_string(ADMIN_CHANNEL_ID), f'InitElection wrong channel: {key[1]}'
                    # assert self.current_phase() == None, f'InitElection during {self.current_phase()}'
                    action = InitElection()
            ioa_triple = (in_match, out_match, action)
            ioa_triples_by_sc[key] = ioa_triple
            # for looking up redeemers of later matches
            if in_match is not None:
                prev_inputs.append(in_match)
            if out_match is not None:
                prev_inputs.append(out_match)
        if ioa_triples_by_sc:
            LOG.debug(f'ioa_triples_by_sc:\n{pformat(ioa_triples_by_sc)}')
        return ioa_triples_by_sc

    def _poll4_fetch_matches(self) -> list[dict]:
        base_params = {"order": "oldest_first"} #, "resolve_hashes": ""} TODO fix this to avoid 400
        
        # TODO merge cursor + etag into the same thing to be sure they change together
        headers = {"If-None-Match": f'{self.etag}'} if self.etag else {}

        r1_params = {} if self.cursor3 is None else {"created_after": self.cursor3}
        r2_params = {} if self.cursor3 is None else {"spent_after":   self.cursor3}
        
        # Q1: new outputs since cursor
        r1 = self.session.get(
            f"{self._kupo_api_url()}/matches",
            params={**base_params, **r1_params},
            headers=headers,
        )
        
        if r1.status_code == 304:
            LOG.debug(f'Got 304 not modified, implying no new matches.')
            return {}

        if r1.status_code == 400:
            raise NotImplementedError("Rollback detected (created_after)")

        r1.raise_for_status()
        LOG.debug(f'r1 headers {r1.headers}')

        # Q2: old inputs now spent since cursor
        r2 = self.session.get(
            f"{self._kupo_api_url()}/matches",
            params={**base_params, **r2_params},
            headers=headers, # TODO did claude forget this? or should it not be there?
        )

        if r2.status_code == 400:
            raise NotImplementedError("Rollback detected (spent_after)")

        r2.raise_for_status()
        LOG.debug(f'r2 headers {r2.headers}')

        # Verify both queries see the same chain tip
        cp1 = r1.headers["X-Most-Recent-Checkpoint"]
        cp2 = r2.headers["X-Most-Recent-Checkpoint"]
        if cp1 != cp2:
            LOG.debug(f'Got 2 different checkpoints: {cp1} vs {cp2}. Retry next poll to avoid edge cases.')
            return {}

        # Merge by (txid, output_index), Q1 and Q2 may overlap
        matches = {}
        for m in r1.json() + r2.json():
            ch_str = kupo_match_to_channel_str(m) 

            created_key = (m['created_at']['slot_no'], ch_str)
            matches[created_key] = m

            if m['spent_at'] is not None:
                spent_key = (m['spent_at']['slot_no'], ch_str)
                matches[spent_key] = m

        if int(cp1) == 0:
            LOG.debug(f'No matches yet. Kupo still starting, or no InitElection yet.')
            assert len(matches) == 0, 'No matches expected before a checkpoint is set.'
            return {}

        # Advance cursor
        try:
            block_hash = r1.headers["ETag"]# .strip('"')
            new_cursor = f"{cp1}.{block_hash}"
            new_etag = r1.headers["ETag"]# .strip('"')
        except KeyError:
            # Kupo doesn't seem to provide ETag (or set a checkpoint?) until a match is found.
            # TODO what should we say/do here?
            LOG.debug(f"chain hasn't advanced, but no 304? Throwing away {len(matches)} matches.")
            return {}

        if new_cursor == self.cursor3 and new_etag == self.etag:
            LOG.debug(f"chain hasn't advanced, but no 304? Throwing away {len(matches)} matches.")
            return {}
            # LOG.debug(f"chain hasn't advanced, but no 304? Processing {len(matches)} matches.")
        else:
            self.cursor3 = new_cursor
            self.etag = new_etag
            LOG.debug(f'advance cursor, etag to {self.cursor3}, {self.etag}. Processing {len(matches)} matches.')
            if matches:
                LOG.debug(f'Processing {len(matches)} merged matches:\n{pformat(matches)}')
            # TODO confirm here that no matches have slots < the old cursor
            # TODO or better that they're all within the window
            return matches


    ## handle election actions ##

    def _on_action(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_action')
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
            # case None:                       LOG.warning(f'event with no action: {event}') # TODO debug
            case _:                          raise NotImplementedError

    def _on_initelection(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_initelection')
        LOG.debug(f'history during _on_initelection:\n{pformat(self.history)}')
        # assert self.history == {}, 'InitElection with non-empty history'
        if self.current_phase() is not None:
            i = event.channel_id
            prev = self.history[i][-1]
            diff = DeepDiff(prev, event)
            LOG.debug(f'diff:\n{pformat(diff)}')
        assert self.current_phase() == None, 'InitElection should always happen first'
        assert event.channel_id == ADMIN_CHANNEL_ID # note this tx was published by the funder
        self._on_mint(event)
        return event

    # remember this will be called once per channel touched
    def _on_addsubchannels(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_addsubchannels')
        if event.channel_id == ADMIN_CHANNEL_ID:
            self._on_cont(event)
        else:
            self._on_mint(event)
        return event

    def _on_advancephase(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_advancephase')
        assert event.channel_id == ADMIN_CHANNEL_ID, 'only admin can advance phase'
        # TODO anything needed here?
        self._on_cont(event)
        return event

    def _on_endelection(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_endelection')
        assert event.channel_id == ADMIN_CHANNEL_ID, 'only admin can end election'
        self._on_burn(event)
        return event

    # remember this will be called once per channel touched
    def _on_rmsubchannels(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_rmsubchannels')
        # assert event.channel_id in self.history, f'tried to remove non-existent channel {event.channel_id}'
        if event.channel_id == ADMIN_CHANNEL_ID:
            self._on_cont(event)
        else:
            self._on_burn(event)
        return event

    # remember this will be called once per channel touched
    def _on_rebalancefunds(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_rebalancefunds')
        self._on_cont(event)
        return event

    def _on_postpublicrecords(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_postpublicrecords')
        # TODO fetch from IPFS here
        self._on_cont(event)
        return event

    def _on_burntesttokens(self, event: ChannelEvent):
        # TODO remove for production use, or make a CLI flag for it
        LOG.debug('ElectionSubscriber._on_burntesttokens')
        self._on_burn(event)
        return event

    def _on_mint(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_mint')
        LOG.debug(f'history during _on_mint:\n{pformat(self.history)}')
        assert not event.channel_id in self.history, f"tried to mint existing channel!\n{event}\n{self.history}"
        self.history[event.channel_id] = [event]

    def _on_burn(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_burn')
        ch_str = channel_id_to_string(event.channel_id)
        assert event.output_state is None, f'{ch_str} being removed, but has an output'
        self.history[event.channel_id].append(event)

    def _on_cont(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_cont')
        assert event.input_match  is not None, 'continuation without input_match'
        assert event.input_state  is not None, 'continuation without input_state'
        assert event.output_match is not None, 'continuation without output_match'
        assert event.output_state is not None, 'continuation without output_state'

        in_seq  = event.input_state.state.seq
        out_seq = event.output_state.state.seq
        assert in_seq + 1 == out_seq, f'state seq error: {in_seq} -> {out_seq} in {event}'

        # TODO put back: assert event.channel_id in self.history, f'_on_cont but {event.channel_id} not in history'
        # if not event.channel_id in self.history:
        #     self.history[event.channel_id] = []

        self.history[event.channel_id].append(event)


    ## handle rollbacks ##

    def _handle_rollback(self):
        raise NotImplementedError

    def _rollback_to(self, safe_slot: int):
        for channel_id, entries in list(self.history.items()):
            kept = [e for e in entries if e.slot_no <= safe_slot]

            if not kept:
                self.history.pop(channel_id)
                # self.current_state.pop(channel_id, None)
                continue

            self.history[channel_id] = kept
            last = kept[-1]

            # Un-burn if the burn was rolled back
            if last.removed_slot is not None and last.removed_slot > safe_slot:
                last.removed_slot = None

            # If channel is live (not burned), make sure it's in current_state
            # if last.removed_slot is None:
            #     self.current_state[channel_id] = (last.utxo, last.state)
            # else:
            #     self.current_state.pop(channel_id, None)
