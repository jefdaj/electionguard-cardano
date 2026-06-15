"""Handles the shared low level details of subscribing to election events.
"""

# TODO use https://pypi.org/project/kupo-py/ ?

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

from dataclasses import dataclass
from os import environ
from pprint import pformat

from typing import Any, Callable, Dict, List, Tuple, Optional, Self

from .ogmios import *
from .plutus.types.channel import *
from .plutus.types.action import *
from .plutus.types.channel import *
from .election import ElectionContext

LOG = logging.getLogger(__name__)

from pycardano import *


# TODO need a different port per instance when running more than one on the same machine?
KUPO_HOST        = environ.get('KUPO_HOST', '127.0.0.1')
KUPO_PORT        = int(environ.get('KUPO_PORT', '1442'))
KUPO_MATCHES_URL = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/matches'


# TODO also use this in subscriberconfig?
@dataclass
class Point:
    slot_no: int
    header_hash: str

    def as_param(self) -> str:
        return f"{self.slot_no}.{self.header_hash}"


@dataclass
class HistoryEntry:
    state: ChannelState
    utxo_dict: dict[str, Any] # TODO fn to convert to pycardano utxo as before
    created_slot: int
    removed_slot: int | None = None # set on final entry when channel is removed


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

# TODO move to channel_id.py
# def channel_id_from_asset_name(encoded: str) -> ChannelId:
#     channel_id = bytes.fromhex(encoded)
#     assert ChannelIdHelper.validate_bytes(channel_id)
#     LOG.debug(f'decoded {asset_name} -> {channel_id}')
#     return channel_id

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

def pycardano_utxo_from_kupo(kupo_dict: dict) -> UTxO:
    """Convert a Kupo UTXO response dict to a PyCardano UTxO.
    WARNING: Does not handle a lot of edge cases! Mainly for BurnTestTokens.
    """
    LOG.debug('ElectionSubscriber.pycardano_utxo_from_kupo')
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


def mk_example_callback(callback_name: str):
    def fn(hist: HistoryEntry) -> None:
        LOG.info(f'{callback_name} called with: {hist}')
    return fn


class ElectionSubscriber:
    '''Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block_hash should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    '''

    def __init__(
            self,
            config: SubscriberConfig,
            on_initelection  = mk_example_callback('on_initelection'),
            on_addsubchannel = mk_example_callback('on_addsubchannel'),
            on_rmsubchannel  = mk_example_callback('on_rmsubchannel'),
            on_endelection   = mk_example_callback('on_endelection'),
        ):

        LOG.debug('ElectionSubscriber.__init__')

        self.config = config

        self.on_initelection  = on_initelection
        self.on_addsubchannel = on_addsubchannel
        self.on_rmsubchannel  = on_rmsubchannel
        self.on_endelection   = on_endelection

        # used to construct channel_ids(), channel_history(), current_state()
        # self.history: Mapping[ChannelId, Mapping[int, ChannelState]] = {}
        self.history: Mapping[ChannelId, list[HistoryEntry]] = {}

        # used to query the current state
        # TODO remove channels from this when they're burned; use history to access after
        # self.states: Mapping[ChannelId, (UTxO, ChannelState)] = {}
        # TODO replace with just getting the latest from the history list or none if burned
        # self.states: Mapping[ChannelId, HistoryEntry] = {}

        # for managing the kupo process
        self._kupo_proc:   Optional[subprocess.Popen] = None
        self._kupo_thread: Optional[threading.Thread] = None
        self._kupo_stop = threading.Event()

        # to prevent duplicate processing of the same transactions
        self._seen_tx_ids: set[str] = set() # TODO remove once sure they're not needed

        # for http requests to the kupo process
        self._session = requests.Session()
        self._session.headers.update({'Accept': 'application/json'})

        # TODO remove
        self._last_tx_key = None

        # The latest created_at.slot_no seen in a result so far.
        # Kupo guarantees ordering by slot when you pass created_after, so
        # dedup-by-id is unnecessary once you only fetch slots strictly after
        # your cursor.
        # TODO hook this up
        self._created_cursor_slot: int = 0   # advance to max(created_at.slot_no) seen


    ## query interface ##

    # self.history and self.states can also be accessed directly
    # TODO write lock just in case that's an issue?

    def channel_ids(self) -> list[ChannelId]:
        LOG.debug('ElectionSubscriber.channel_ids')
        return sorted(self.history.keys())

    def channel_history(self, channel_id: ChannelId) -> list[HistoryEntry]:
        LOG.debug('ElectionSubscriber.channel_history')
        return self.history[channel_id] # TODO return None rather than raise KeyError?

        # LOG.debug(f'history: {self.history}')
        # records = []
        # TODO fix so even if one is missing, iteration doesn't get messed up
        # if not channel_id in self.history:
        #     return []
        # for seq in range(0, len(self.history[channel_id])):
        #     assert seq in self.history[channel_id], f'Missing records with channel_id={channel_id} seq={seq}.'
        #     records += list(self.history[channel_id][seq].state.new_records)
        # return records

    def channel_state(self, channel_id: ChannelId) -> HistoryEntry:
        LOG.debug('ElectionSubscriber.channel_state')
        return self.channel_history(channel_id)[-1] # TODO return None rather than raise KeyError?


    ## process managment interface ##

    def start(self) -> None:
        LOG.debug('ElectionSubscriber.start')
        self._kupo_stop.clear()

        def _start_and_watch() -> None:
            try:
                self._start_kupo()
                self._watch_kupo()
            except Exception as e:
                LOG.error(f'Error in watcher: {e}')

        def handle_sigint(sig, frame):
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
        LOG.debug('ElectionSubscriber.join')
        # TODO how is this actually supposed to be done?
        while not self.is_done():
            time.sleep(1)

    def stop(self) -> None:
        LOG.debug('ElectionSubscriber.stop')
        self._stop_kupo()
        self._kupo_stop.set()
        if self._kupo_thread and self._kupo_thread.is_alive():
            LOG.debug('Waiting for watcher thread to exit...')
            try:
                self._kupo_thread.join(timeout=5)
            except Exception as e:
                if not 'cannot join current thread' in str(e):
                    raise
        self._kupo_thread = None

    def is_done(self):
        LOG.debug('ElectionSubscriber.is_done')
        return self._kupo_stop.is_set() \
           and self._kupo_thread is None


    ## process management guts ##

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

    def _start_kupo(self) -> None:
        '''
        Start Kupo as a subprocess.
        Uses `--since {slot}.{hash}` and `--match '{policy_id}/*'`.
        '''
        LOG.debug('ElectionSubscriber._start_kupo')

        if self._kupo_proc is not None and self._kupo_proc.poll() is None:
            LOG.warning(f'Kupo already running (pid={self._kupo_proc.pid})')
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

        cmd += [

            '--match', f'{self.config.policy_id}/*',

            '--host', KUPO_HOST,
            '--port', str(KUPO_PORT),

            '--log-level', 'Warning'

            # '--prune-utxo',

            # TODO is any margin needed in this case?
            # '--safety-margin', '100',

        ]

        LOG.debug(f'Starting Kupo: {' '.join(cmd)}')
        self._kupo_proc = subprocess.Popen(
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
        # TODO why does this seem to happen immediately?
        LOG.debug('Kupo subprocess output thread terminating')

    def _stop_kupo(self) -> None:
        LOG.debug('ElectionSubscriber._stop_kupo')

        proc = self._kupo_proc
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

        self._kupo_proc = None

    def _watch_kupo(self) -> None:
        LOG.debug('ElectionSubscriber._watch_kupo')
        LOG.debug(f'Watcher thread started for policy_id={self.config.policy_id}')

        while not self._kupo_stop.is_set():
            try:
                resp = self._session.get(
                    KUPO_MATCHES_URL,
                    timeout=10,
                    params={
                        'with_spent': 'true',
                        'order': 'oldest_first',
                    }
                )
                resp.raise_for_status()
                utxo_dicts = resp.json()
                # LOG.debug(f'resp.json:\n{json.dumps(utxo_dicts, indent=2)}')

                if not isinstance(utxo_dicts, list):
                    raise Exception(f'Unexpected Kupo response type: {type(utxo_dicts)}')

                for utxo_dict in utxo_dicts:
                    if not isinstance(utxo_dict, dict):
                        raise Exception(f'Unexpected utxo format {type(utxo_dict)}:\n{utxo_dict}')

                    self._on_utxo(utxo_dict)

            except requests.RequestException as e:
                LOG.debug(f'Kupo polling error: {e}') # TODO back to warning?
                time.sleep(5)
            except Exception as e:
                LOG.error(f'Unexpected error in watcher: {e} {type(e)}')
                time.sleep(5)

            time.sleep(OGMIOS_POLL_SEC)

        LOG.debug('Watcher thread exiting')


    ## election state management guts ##

    def _on_utxo(self, utxo_dict: dict[str, Any]):
        LOG.debug('ElectionSubscriber._on_utxo')
        LOG.debug(f'utxo_dict: {pformat(utxo_dict)}')
        # skip already-processed transactions
        # TODO is this ever actually needed?
        # TODO is this wrong in case of a roll-back?
        tx_id = utxo_dict.get('transaction_id')
        out_ix = utxo_dict.get('output_index')
        key = (tx_id, out_ix)
        if tx_id and key in self._seen_tx_ids:
            return
        if tx_id:
            # LOG.debug(f'last_tx_key: {key}')
            self._seen_tx_ids.add(key)
            self._last_tx_key = key
            # any_new_utxo = True

        try:
            (channel_id, hist) = self._parse_history_entry(utxo_dict)
            LOG.debug(f'channel_id: {channel_id} ({type(channel_id)})')
            LOG.debug(f'hist: {hist} ({type(hist)})')
            channel_added = bool(not channel_id in self.history)
            if channel_added:
                self.history[channel_id] = []
            self.history[channel_id].append(hist)
            if channel_added:
                if channel_id == ADMIN_CHANNEL_ID:
                    self.on_initelection(hist)
                else:
                    self.on_addsubchannel(hist)
        except Exception as e:
            LOG.error(f'Error in self._parse_history_entry: {e}')

    def _fetch_datum(self, datum_hash: str) -> Any:
        LOG.debug('ElectionSubscriber._fetch_datum')
        url = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/datums/{datum_hash}' # TODO global var?
        LOG.debug(f'fetching datum {datum_hash}')
        resp = self._session.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _parse_history_entry(self, utxo_dict: Dict[str, Any]) -> (ChannelId, HistoryEntry):
        LOG.debug('ElectionSubscriber._parse_history_entry')
        LOG.debug(f'utxo_dict:\n{json.dumps(utxo_dict, indent=2)}')

        tx_id       = utxo_dict.get('transaction_id')
        out_ix      = utxo_dict.get('output_index')
        datum_hash  = utxo_dict.get('datum_hash')
        datum_type  = utxo_dict.get('datum_type')
        created     = utxo_dict.get('created_at') # TODO is it ever not there? or {}
        created_slot = int(created.get('slot_no'))
        header_hash = created.get('header_hash')

        assert datum_hash # TODO will this not exist in the final EndElection tx?

        try:
            datum = self._fetch_datum(datum_hash)

            # try subchannel first because that should be more common long term
            try:
                state = SubChannel.from_cbor(datum['datum'])
                channel_id = state.state.channel_id
            except:

                # TODO would a minimal, messy fix be to check for channels removed here?

                state = AdminChannel.from_cbor(datum['datum'])
                channel_id = ADMIN_CHANNEL_ID

            ch_str = channel_id_to_string(channel_id)
            LOG.debug(f'decoded {ch_str} state {state.state.seq}: {state}')

            hist = HistoryEntry(
                state         = state,
                utxo_dict     = utxo_dict,
                created_slot  = created_slot,
                removed_slot  = None, # will be filled in by _on_spend later
            )
            LOG.debug(f'hist: {hist}')

            return (channel_id, hist)

        except Exception as e:
            LOG.error(f'handle_match: failed to fetch datum {datum_hash}: {e}')
            raise

    # TODO remove?
    def _on_close(self, utxo: Dict[str, Any]) -> ElectionAction:
        LOG.debug('handle_endelection: admin channel closed')
        return EndElection()

    def _check_if_admin_channel_closed(self):
        LOG.debug('ElectionSubscriber.check_if_admin_channel_closed')
        if self._last_tx_key is None:
            LOG.debug('no transactions have been published yet?')
            return
        (tx_id, output_ix) = self._last_tx_key
        resp = self._session.get(KUPO_MATCHES_URL + f'/{output_ix}@{tx_id}') # TODO params? timeout?
        if resp.status_code == 200:
            utxos = resp.json() # TODO store a map of channel id -> latest utxo in the subscriber
            LOG.debug(f'utxos: {pformat(utxos)}')
            assert isinstance(utxos, list), "expected a list of UTXOs"
            for utxo in utxos:
                # There should only be one
                # TODO update to handle subchannels
                # TODO later, update to handle reference script utxo
                if 'spent_at' in utxo and utxo['spent_at'] is not None:
                    LOG.debug(f'Confirmed: STT UTXO spent without creating a new one.')
                    self._on_close(utxo)
                    self.stop()
                    return
        LOG.debug(f'Channel not yet closed {resp}')

    def _rollback_to(self, safe_slot: int):
        for channel_id, entries in list(self.history.items()):
            kept = [e for e in entries if e.created_slot <= safe_slot]

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
