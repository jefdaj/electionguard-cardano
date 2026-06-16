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

from urllib.parse import urlencode
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

    # Not used yet, but may be useful for display in an interface.
    # The first of these per channel should be from the unspent matches,
    # and then the rest should be from spent matches. We could update the
    # unspent one -> spent after it's spent, but I don't see a need so far.
    # TODO would it be easy to pop and re-add the initial one on spend?
    kupo_match: dict[str, Any]

    # The last of these per channel should be None,
    # signifying the channel was closed (burned).
    state: Optional[ChannelState]

    # Should always exist.
    action: ElectionAction


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

def is_port_in_use(port: int) -> bool:
    # based on https://stackoverflow.com/a/52872579
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((KUPO_HOST, port)) == 0

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


def find_redeemer(kupo_match, kupo_matches) -> Optional[ElectionAction]:
    "Search kupo_matches for a `spent_at` matching the current match."
    tx_id = kupo_match.get('transaction_id')
    # TODO in this contract, is tx_id all we need? aka one action per tx?
    # tx_ix = kupo_match.get('output_index') # TODO is this right?
    for m in kupo_matches:
        try:
            spent = m.get('spent_at')
        except:
            continue
        # TODO check if tx matches first, then get redeemer if so
        if spent['transaction_id'] == tx_id: # and spent['input_index'] == tx_ix:
            cbor = spent['redeemer']
            redeemer = decode_plutusdata_union(ElectionAction, cbor)
            LOG.debug(f'matching redeemer: {redeemer}')
            return redeemer
    return None

def mk_example_callback(callback_name: str):
    def fn(event: ChannelEvent) -> None:
        LOG.info(f'{callback_name} called with: {event}')
    return fn

def spent_unspent_pairs(spent, unspent):
    # 1. make set of keys: slot + tx id + index? (fn for this)
    # 2. use that to make (unspent, spent) pairs where one or the other may be None
    # TODO itertools.groupby first, then make pairs explicit
    raise NotImplementedError

def find_redeemers(matches: list[dict]) -> list[Tuple[ElectionAction, dict]]:
    with_redeemers: Tuple[ElectionAction, dict] = []
    for match in matches:
        redeemer = find_redeemer(match, matches)
        if redeemer is None:
            # Should only happen with the first TX, because the oneshot
            # UTXO doesn't carry an STT and so doesn't match the Kupo
            # pattern.
            # assert len(self.history) == 0
            assert match == matches[0]
            redeemer = InitElection()
        with_redeemers.append((redeemer, match))
    LOG.debug(f'with_redeemers {len(with_redeemers)}: {pformat(with_redeemers)}')
    assert len(with_redeemers) == len(matches)
    return with_redeemers



class ElectionSubscriber:
    '''Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block_hash should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    '''

    def __init__(
            self,
            config: SubscriberConfig,
            on_initelection      = mk_example_callback('on_initelection'),
            on_postpublicrecords = mk_example_callback('on_postpublicrecords'),
            on_advancephase      = mk_example_callback('on_advancephase'),
            on_addsubchannel     = mk_example_callback('on_addsubchannel'),
            on_rmsubchannel      = mk_example_callback('on_rmsubchannel'),
            on_endelection       = mk_example_callback('on_endelection'),
            on_rollback          = mk_example_callback('on_rollback'),
        ):

        LOG.debug('ElectionSubscriber.__init__')

        self.config = config

        # High-level callbacks
        self.on_initelection      = on_initelection
        self.on_postpublicrecords = on_postpublicrecords
        self.on_advancephase      = on_advancephase
        self.on_addsubchannel     = on_addsubchannel
        self.on_rmsubchannel      = on_rmsubchannel
        self.on_endelection       = on_endelection
        self.on_rollback          = on_rollback

        # State is split into current and historical, because that makes it
        # simpler to work with Kupo's spent and unspent UTXO filters. When a
        # UTXO is spent we remove it from current and append its new spent
        # equivalent to history.
        # TODO helpful, or no? history isn't immutible so it would be fine to mix them
        self.current: Mapping[ChannelId, ChannelEvent] = {}
        self.history: Mapping[ChannelId, list[ChannelEvent]] = {}

        # used to query the current state
        # TODO remove channels from this when they're burned; use history to access after
        # self.states: Mapping[ChannelId, (UTxO, ChannelState)] = {}
        # TODO replace with just getting the latest from the history list or none if burned
        # self.states: Mapping[ChannelId, ChannelEvent] = {}

        # for managing the kupo process
        self.kupo_proc:   Optional[subprocess.Popen] = None
        self.kupo_thread: Optional[threading.Thread] = None
        self.kupo_stop = threading.Event()

        # this will be updated when starting kupo to avoid conflicts with existing processes
        self.kupo_port = KUPO_PORT

        # to prevent duplicate processing of the same transactions
        # self._seen_tx_ids: set[str] = set() # TODO remove once sure they're not needed

        # for http requests to the kupo process
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

        # TODO remove
        # self._last_tx_key = None

        # For reducing duplicate matches and handling rollbacks
        # TODO only need one?
        # self.created_cursor: Optional[Point] = None
        # self.spent_cursor:   Optional[Point] = None

        # Starting at the point from the config seems logical,
        # but for some reason Kupo rejects it. None works fine.
        # self.cursor = Point.from_config(self.config)
        self.cursor = None

        # Track unspent UTxOs we care about so we can detect spends
        # TODO remove?
        # self.tracked: dict[str, dict] = {}  # key: f"{tx_id}#{output_index}"


    ## query interface ##

    # self.history and self.states can also be accessed directly
    # TODO write lock just in case that's an issue?

    def channel_ids(self) -> list[ChannelId]:
        LOG.debug('ElectionSubscriber.channel_ids')
        return sorted(self.history.keys())

    def channel_history(self, channel_id: ChannelId) -> list[ChannelEvent]:
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

    def channel_state(self, channel_id: ChannelId) -> ChannelEvent:
        LOG.debug('ElectionSubscriber.channel_state')
        return self.channel_history(channel_id)[-1] # TODO return None rather than raise KeyError?


    ## process managment interface ##

    def start(self) -> None:
        LOG.debug('ElectionSubscriber.start')
        self.kupo_stop.clear()

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

        self.kupo_thread = threading.Thread(
            target=_start_and_watch,
            daemon=False,
        )
        self.kupo_thread.start()

    def join(self):
        LOG.debug('ElectionSubscriber.join')
        # TODO how is this actually supposed to be done?
        while not self.is_done():
            time.sleep(1)

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
                self._poll_attempt2()
            except requests.RequestException as e:
                LOG.warning(f'Kupo polling error: {e}') # TODO error?
            except Exception as e:
                LOG.error(f'Unexpected error in watcher: {e} {type(e)}')
                raise
            finally:
                time.sleep(OGMIOS_POLL_SEC)
        LOG.debug('Watcher thread exiting')


    ## election state management ##

    def _on_match(self, kupo_match: dict[str, Any]):
        LOG.debug('ElectionSubscriber._on_match')
        LOG.debug(f'kupo_match: {pformat(kupo_match)}')

        try:
            (channel_id, event) = self._parse_event(kupo_match)
            LOG.debug(f'channel_id: {channel_id} ({type(channel_id)})')
            LOG.debug(f'event: {event} ({type(event)})')
            channel_added = bool(not channel_id in self.history)
            if channel_added:
                self.history[channel_id] = []
            self.history[channel_id].append(hist)
            if channel_added:
                if channel_id == ADMIN_CHANNEL_ID:
                    self.on_initelection(event)
                else:
                    self.on_addsubchannel(event)
        except Exception as e:
            LOG.error(f'Error in self._parse_event: {e}')

    def _fetch_datum(self, datum_hash: str) -> Any:
        LOG.debug('ElectionSubscriber._fetch_datum')
        url = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/datums/{datum_hash}' # TODO global var?
        LOG.debug(f'fetching datum {datum_hash}')
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _parse_event(self, kupo_match: Dict[str, Any]) -> (ChannelId, ChannelEvent):
        LOG.debug('ElectionSubscriber._parse_event')
        LOG.debug(f'kupo_match:\n{json.dumps(kupo_match, indent=2)}')

        tx_id       = kupo_match.get('transaction_id')
        out_ix      = kupo_match.get('output_index')
        datum_hash  = kupo_match.get('datum_hash')
        datum_type  = kupo_match.get('datum_type')
        created     = kupo_match.get('created_at') # TODO is it ever not there? or {}
        slot_no = int(created.get('slot_no'))
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
            
            try:
                # TODO is this the redeemer for the NEXT transaction?
                created = kupo_match.get('spent_at')
                LOG.debug(f'created: {created}')
                redeemer_cbor = created['redeemer']
                LOG.debug(f'redeemer_cbor: {redeemer_cbor}')
                # TODO skip if None or whatever on the last one?
                action = decode_plutusdata_union(ElectionAction, redeemer_cbor)
                LOG.debug(f'decoded {ch_str} action: {action}')
            except:
                LOG.debug(f'Failed ot decode {ch_str} action')
                action = None

            event = ChannelEvent(
                slot_no       = slot_no,
                kupo_match    = kupo_match,
                state         = state,
                action        = action,
            )
            LOG.debug(f'event: {event}')

            return (channel_id, event)

        except Exception as e:
            LOG.error(f'handle_match: failed to fetch datum {datum_hash}: {e}')
            raise

    def _matches_url(self) -> str:
        LOG.debug('ElectionSubscriber._matches_url')
        return f'http://{KUPO_HOST}:{self.kupo_port}/v1/matches'

#     def _poll(self):
# 
#         LOG.debug('ElectionSubscriber._poll')
#         params = {"order": "oldest_first"}
#         if self.cursor:
#             # TODO test this with in-progress elections
#             params["created_after"] = self.cursor.as_param()
# 
#         r = self.session.get(self._matches_url(), params=params)
#         LOG.debug(f'r.json: {json.dumps(r.json(), indent=2)}')
# 
#         if r.status_code == 400:
#             # Cursor point no longer on chain — rollback past our cursor
#             self._handle_rollback()
#             return
#         r.raise_for_status()
# 
#         # experimental new stuff
#         matches = r.json()
#         LOG.debug(f'matches: {json.dumps(matches, indent=2)}')
#         with_redeemers: Tuple[ElectionAction, dict] = []
#         for match in matches:
#             redeemer = find_redeemer(match, matches)
#             if redeemer is None:
#                 # Should only happen with the first TX, because the oneshot
#                 # UTXO doesn't carry an STT and so doesn't match the Kupo
#                 # pattern.
#                 assert len(self.history) == 0
#                 assert match == matches[0]
#                 redeemer = InitElection()
#             with_redeemers.append((redeemer, match))
#         LOG.debug(f'with_redeemers {len(with_redeemers)}: {pformat(with_redeemers)}')
#         assert len(with_redeemers) == len(matches)
# 
#         for utxo in r.json():
#             self._on_match(utxo)
#             self.created_cursor = Point(
#                 utxo["created_at"]["slot_no"],
#                 utxo["created_at"]["header_hash"],
#             )

    def _poll_attempt2(self):
        # Spent UTXOs are better in general because they have more info:
        # - spent_at of course, which isn't really used so far
        # - also the spending redeemer (to detect burns, to add to next event)

        LOG.debug('ElectionSubscriber._poll_attempt2')
        params = {"order": "oldest_first"}

        # TODO are there any edge cases where order matters here?
        # First instinct: spent is safer to start with, because then we
        # probably can't get one that was spent but not created yet?
        spent   = self._fetch_spent()
        unspent = self._fetch_unspent()

        if not spent and not unspent:
            return

        (spent, unspent) = self._update_cursor_and_truncate(spent, unspent)

        # TODO which step is best to look up redeemers?
        #      I guess the almost-final version, but look up redeemers from spent only?

        pairs = spent_unspent_pairs(spent, unspent)

        # TODO case analysis on pairs:
        #      - created only -> mint -> current state new, confirm no channel history
        #                                also check for InitElection special case
        #      - both -> continuation -> current state new, append spent to history
        #                                get redeemer just to have the info
        #      - spent only -> burn -> current state None, append spent to history
        #                              get redeemer and confirm it's a burn

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

    def _fetch_spent(self):
        LOG.debug('ElectionSubscriber._fetch_spent')
        params = {"order": "oldest_first"}
        if self.cursor:
            params["spent_after"] = self.cursor.as_param()
        url = self._matches_url() + "?" + urlencode(params) + "&spent"
        r = self.session.get(url)
        if r.status_code == 400:
            # Cursor point no longer on chain — rollback past our cursor
            self._handle_rollback()
            return
        r.raise_for_status()
        matches = r.json()
        LOG.debug(f'spent matches: {json.dumps(matches, indent=2)}')
        return matches

    def _fetch_unspent(self):
        LOG.debug('ElectionSubscriber._fetch_unspent')
        params = {"order": "oldest_first"}
        if self.cursor:
            params["created_after"] = self.cursor.as_param()
        url = self._matches_url() + "?" + urlencode(params) + "&unspent"
        r = self.session.get(url)
        if r.status_code == 400:
            # Cursor point no longer on chain — rollback past our cursor
            self._handle_rollback()
            return
        r.raise_for_status()
        matches = r.json()
        LOG.debug(f'unspent matches: {json.dumps(matches, indent=2)}')
        return matches

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
