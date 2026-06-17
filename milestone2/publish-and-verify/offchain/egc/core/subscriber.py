import socket
import argparse
import json
import os
import requests
import signal
import subprocess
import sys
import threading
import time
import logging
import itertools
from copy import copy

from urllib.parse import urlencode
from dataclasses import dataclass, replace
from os import environ
from pprint import pformat
from collections import defaultdict

from typing import Any, Callable, Dict, List, Tuple, Optional, Self

from .ogmios import *
from .plutus.types.channel import *
from .plutus.types.action import *
from .plutus.types.channel import *
from .election import ElectionContext

LOG = logging.getLogger(__name__)

from pycardano import *

# TODO use https://pypi.org/project/kupo-py/ ?


# TODO need a different port per instance when running more than one on the same machine?
KUPO_HOST        = environ.get('KUPO_HOST', '127.0.0.1')
KUPO_PORT        = int(environ.get('KUPO_PORT', '1442'))



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

    # Mints have only outputs, burns have only inputs, and continutations have both.
    input_match:  Optional[dict[str, Any]]
    output_match: Optional[dict[str, Any]]

    # Mints have only outputs, burns have only inputs, and continutations have both.
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


def find_redeemer(kupo_match, spent_matches) -> Optional[ElectionAction]:
    "Search spent_matches for a `spent_at` matching the current match."
    tx_id = kupo_match.get('transaction_id')
    # TODO in this contract, is tx_id all we need? aka one action per tx?
    # tx_ix = kupo_match.get('output_index') # TODO is this right?
    for m in spent_matches:
        spent = m.get('spent_at')
        if spent['transaction_id'] == tx_id: # and spent['input_index'] == tx_ix:
            LOG.debug(f'matching spent json: {spent}')
            cbor = spent['redeemer']
            redeemer = decode_plutusdata_union(ElectionAction, cbor)
            LOG.debug(f'matching redeemer: {redeemer}')
            return redeemer
    LOG.warning(f'No matching redeemer for: {kupo_match}')
    return None

def mk_example_callback(callback_name: str):
    def fn(event: ChannelEvent) -> None:
        print(f'{callback_name} called with:\n{pformat(event)}')
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
    if new_event.output_match is None or new_event.output_match['spent_at'] is None:
        return False
    old_output_match_spent = copy(old_event.output_match)
    old_output_match_spent['spent_at'] = copy(new_event.output_match['spent_at'])
    old_event_spent = replace(old_event, output_match=old_output_match_spent)
    return old_event_spent == new_event


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
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

        # Starting at the point from the config seems logical,
        # but for some reason Kupo rejects it. None works fine.
        # self.cursor = Point.from_config(self.config)
        self.cursor = None

        # For debugging.
        self.prev_events = set()


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
        return event.output_state # may also be None

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

        time.sleep(0.1) # prevents polling error during startup

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
                self._poll()
            except requests.RequestException as e:
                LOG.warning(f'Kupo polling error: {e}') # TODO error?
            except Exception as e:
                LOG.error(f'Unexpected error in watcher: {e} {type(e)}', exc_info=True)
                raise
            finally:
                time.sleep(OGMIOS_POLL_SEC)
        LOG.debug('Watcher thread exiting')


    ## polling and http queries ##

    def _poll(self):
        # Spent UTXOs are better in general because they have more info:
        # - spent_at of course, which isn't really used so far
        # - also the spending redeemer (to detect burns, to add to next event)

        LOG.debug('ElectionSubscriber._poll')
        params = {"order": "oldest_first"}

        # TODO are there any edge cases where order matters here?
        # First instinct: spent is safer to start with, because then we
        # probably can't get one that was spent but not created yet?
        LOG.debug(f'fetching with cursor {self.cursor}')
        spent   = self._fetch_spent()
        unspent = self._fetch_unspent()

        if not spent and not unspent:
            return

        (spent, unspent) = self._update_cursor_and_truncate(spent, unspent)

        all_spent = self._add_old_spent(spent)
        pairs_by_key = input_output_pairs(all_spent, unspent) # TODO make a method?

        for event in self._channel_events(pairs_by_key, all_spent):

            # TODO is there a cleaner way to do this?
            i = event.channel_id
            if i in self.history and len(self.history[i]) > 0:
                prev_event = self.history[i][-1]
                if _same_but_now_spent(prev_event, event):
                    s = channel_id_to_string(i)
                    self.history[i][-1] = event
                    LOG.debug(f'Replaced last {s} event with a new spent version.')
                    continue

            # TODO less similar names?
            self._on_action(event) # internal callback
            self.on_action(event)  # external callback

    def _add_old_spent(self, new_spent):
        LOG.debug('ElectionSubscriber._add_old_spent')
        # have to bring back prev spent matches here too,
        # because the relevant ones may be in a prev batch
        # TODO is that also important for the input_output_pairs?
        old_event = [x for sub in self.history.values() for x in sub]
        # events = [c[-1] for c in self.history.values()]
        old_spent = [e.input_match for e in old_event if e.input_match is not None]
        LOG.debug(f'old_spent: {old_spent}')
        return old_spent + new_spent

    def _kupo_api_url(self) -> str:
        LOG.debug('ElectionSubscriber._kupo_api_url')
        return f'http://{KUPO_HOST}:{self.kupo_port}/v1'

    def _fetch_spent(self):
        LOG.debug('ElectionSubscriber._fetch_spent')
        params = {"order": "oldest_first"}
        if self.cursor is not None:
            params["spent_after"] = self.cursor.as_param()
        url = self._kupo_api_url() + "/matches?" + urlencode(params) + "&spent"
        r = self.session.get(url)
        if r.status_code == 400:
            # Cursor point no longer on chain — rollback past our cursor
            # TODO retry first? seems to happen transiently sometimes?
            self._handle_rollback()
            return
        r.raise_for_status()
        matches = r.json()
        if self.cursor is not None:
            # kupo returns matches inclusive? we don't want the duplicates
            matches = [m for m in matches if m['spent_at']['slot_no'] > self.cursor.slot_no]
        LOG.debug(f'spent matches: {json.dumps(matches, indent=2)}')
        return matches

    def _fetch_unspent(self):
        LOG.debug('ElectionSubscriber._fetch_unspent')
        params = {"order": "oldest_first"}
        if self.cursor is not None:
            params["created_after"] = self.cursor.as_param()
        url = self._kupo_api_url() + "/matches?" + urlencode(params) + "&unspent"
        r = self.session.get(url)
        if r.status_code == 400:
            # Cursor point no longer on chain — rollback past our cursor
            self._handle_rollback()
            return
        r.raise_for_status()
        matches = r.json()
        if self.cursor is not None:
            # kupo returns matches inclusive? we don't want the duplicates
            matches = [m for m in matches if m['created_at']['slot_no'] > self.cursor.slot_no]
        LOG.debug(f'unspent matches: {json.dumps(matches, indent=2)}')
        return matches

    def _update_cursor_and_truncate(self, spent, unspent):
        LOG.debug('ElectionSubscriber._update_cursor_and_truncate')

        # get the latest point from each list
        last_spent   = None if not spent   else Point.from_kupo_resp(spent[-1]['spent_at'])
        last_unspent = None if not unspent else Point.from_kupo_resp(unspent[-1]['created_at'])
        LOG.debug(f'last_spent: {last_spent}')
        LOG.debug(f'last_unspent: {last_unspent}')

        # if they both have a last one, use the earlier
        # TODO is this necessary? not sure if they're guaranteed to be the same
        points = [p for p in (last_spent, last_unspent) if p is not None]
        earlier = min(points, key=lambda p: p.slot_no)
        LOG.debug(f'earlier: {earlier}')

        # cut off utxos after that from both lists (only one will have any),
        # so they can be processed next poll loop without duplicate events
        LOG.debug(f'lengths before truncation: spent={len(spent)}, unspent={len(unspent)}')
        spent   = [m for m in spent   if m['spent_at'  ]['slot_no'] <= earlier.slot_no]
        unspent = [m for m in unspent if m['created_at']['slot_no'] <= earlier.slot_no]
        LOG.debug(f'lengths after truncation: spent={len(spent)}, unspent={len(unspent)}')

        # update cursor to the earlier so that the cut-off values will be
        # fetched again next poll
        self.cursor = earlier
        LOG.debug(f'updated cursor to {earlier}')

        return (spent, unspent)

    def _fetch_datum(self, datum_hash: str) -> Any:
        LOG.debug('ElectionSubscriber._fetch_datum')
        # TODO adjust to port changes
        url = self._kupo_api_url() + f'/datums/{datum_hash}'
        LOG.debug(f'fetching datum {datum_hash}')
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _channel_events(self, pairs_by_key, spent) -> list[ChannelEvent]:
        LOG.debug('channel_events')
        events = []
        keys = sorted(pairs_by_key.keys())
        first_event = True
        for key in keys:
            LOG.debug(f'key: {key}')

            (slot_no, channel_str) = key
            LOG.debug(f'slot_no: {slot_no}')
            LOG.debug(f'channel_str: {channel_str}')

            (input_match, output_match) = pairs_by_key[key]
            LOG.debug(f'input_match: {input_match}')
            LOG.debug(f'output_match: {output_match}')

            assert input_match is not None or output_match is not None, 'input and output matches cannot both be None'

            # Get states (AKA datums)
            if input_match is not None:
                input_datum = self._fetch_datum(input_match['datum_hash'])['datum']
                input_state = decode_plutusdata_union(ChannelState, input_datum)
            else:
                input_state = None
            if output_match is not None:
                output_datum = self._fetch_datum(output_match['datum_hash'])['datum']
                output_state = decode_plutusdata_union(ChannelState, output_datum)
            else:
                output_state = None

            # Get action (AKA redeemer)
            if output_match is not None:
                if input_match is None:
                    all_spent = spent
                else:
                    all_spent = spent + [input_match]
                action = find_redeemer(output_match, all_spent)
                LOG.debug(f'action: {action}')
                if action is None:
                    # Should only happen in the very first event, because the input
                    # (the one-shot UTXO) doesn't have an STT and so doesn't match the
                    # Kupo filter.
                    assert channel_str == 'admin'
                    assert input_state is None
                    assert isinstance(output_state.state, AdminChannelState)
                    # assert output_state.state.seq == 0, f'output_state seq != 0: {output_state}'
                    action = InitElection()
                assert action is not None
            else:
                action = None

            event = ChannelEvent(
                slot_no      = slot_no,
                channel_id   = coerce_channel_id(channel_str),
                action       = action,
                input_match  = input_match,
                output_match = output_match,
                input_state  = input_state,
                output_state = output_state,
            )
            LOG.debug(f'event:\n{pformat(event)}')

            if str(event) in self.prev_events:
                LOG.error(f'duplicate event: {event}')
            self.prev_events.add(str(event))

            events.append(event)
        return events


    ## handle election actions ##

    def _on_action(self, event: ChannelEvent):
        match event.action:
            case InitElection():             self._on_initelection(event)
            case AddSubChannels(channels):   self._on_addsubchannels(event)
            case AdvancePhase():             self._on_advancephase(event)
            case EndElection():              self._on_endelection(event)
            case RmSubChannels(channels=_):  self._on_rmsubchannels(event)
            case RebalanceFunds(channels=_): self._on_rebalancefunds(event)
            case PostPublicRecords():        self._on_postpublicrecords(event)
            case BurnTestTokens():           self._on_burntesttokens(event)
            case None:                       LOG.error(f'event with no action: {event}')
            case _:                          raise NotImplementedError

    def _on_initelection(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_initelection')
        # assert self.history == {}, 'InitElection with non-empty history'
        # there might be history already if the subscriber processed a different channel event first?
        LOG.debug(f'history during _on_initelection:\n{pformat(self.history)}')
        assert event.channel_id == ADMIN_CHANNEL_ID # note this tx was published by the funder
        self._on_mint(event)

    # remember this will be called once per channel touched
    def _on_addsubchannels(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_addsubchannels')
        if event.channel_id == ADMIN_CHANNEL_ID:
            self._on_cont(event)
        else:
            self._on_mint(event)

    def _on_advancephase(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_advancephase')
        assert event.channel_id == ADMIN_CHANNEL_ID, 'only admin can advance phase'
        # TODO anything needed here?
        self._on_cont(event)

    def _on_endelection(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_endelection')
        assert event.channel_id == ADMIN_CHANNEL_ID, 'only admin can end election'
        self._on_burn(event)

    # remember this will be called once per channel touched
    def _on_rmsubchannels(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_rmsubchannels')
        assert event.channel_id in self.history, f'tried to remove non-existent channel {ch_str}'
        if event.channel_id == ADMIN_CHANNEL_ID:
            self._on_cont(event)
        else:
            self._on_burn(event)

    # remember this will be called once per channel touched
    def _on_rebalancefunds(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_rebalancefunds')
        self._on_cont(event)

    def _on_postpublicrecords(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_postpublicrecords')
        # TODO fetch from IPFS here
        self._on_cont(event)

    def _on_burntesttokens(self, event: ChannelEvent):
        # TODO remove for production use, or make a CLI flag for it
        LOG.debug('ElectionSubscriber._on_burntesttokens')
        self._on_burn(event)

    def _on_mint(self, event: ChannelEvent):
        LOG.debug('ElectionSubscriber._on_mint')
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

        in_seq  = input_state.state.seq
        out_seq = output_state.state.seq
        assert in_seq + 1 == out_seq, f'state seq error: {in_seq} -> {out_seq} in {event}'

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
