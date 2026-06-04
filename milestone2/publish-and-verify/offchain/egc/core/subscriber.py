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

from .ogmios import OGMIOS_HOST, OGMIOS_PORT
from .plutus.types.channel import *
from .plutus.types.action import *
from .plutus.types.channel import *
from .election import ElectionContext

LOG = logging.getLogger(__name__)

from pycardano import *


KUPO_HOST        = environ.get('KUPO_HOST', '127.0.0.1')
KUPO_PORT        = int(environ.get('KUPO_PORT', '1442'))
KUPO_MATCHES_URL = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/matches'

# How often to poll the local Ogmios instance for new UTxOs.
# TODO what's reasonable?
KUPO_POLL_SEC = 0.5

# Approximate upper limit of how long it might take to propagate transactions
# to subscribers.
# TODO how to estimate this when using the testnet?
KUPO_DELAY_SEC = 3

# TODO pull this from ogmios module, and rename
NODE_SOCKET = environ.get('CARDANO_NODE_SOCKET_PATH', '../../cardano-node-ogmios/data/node-ipc/node.socket')
NODE_CONFIG = environ.get('NODE_CONFIG', '../../cardano-node-ogmios/config/network/preview/cardano-node/config.json')

@dataclass
class SubscriberConfig:
    since_slot:  int # For kupo --since
    since_block_hash: str # For kupo --since
    policy_id:   str # For kupo --match TODO remove?
    until_slot: Optional[int] = None # For kupo --until, to prevent open-ended scans during tests

    @classmethod
    def from_election(cls, election: ElectionContext) -> Self:
        return cls(
            election.deployment.index_from_slot,
            election.deployment.index_from_block_hash,
            str(election.script.policy_id), # TODO use the pycardano object?
            None,
        )

# Handles a single kupo match response json obj.
# TODO can the response type be more specific than dict?
SubscriberCallback = Callable[[dict, requests.Session], ElectionAction]

def fetch_datum(session: requests.Session, datum_hash: str) -> Any:
    url = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/datums/{datum_hash}' # TODO global var?
    LOG.debug(f'fetch_datum: fetching datum {datum_hash}')
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

# TODO remove? merge into Subscriber class?
def handle_endelection(utxo: Dict[str, Any], session: requests.Session) -> ElectionAction:
    LOG.info('handle_endelection: admin channel closed')
    return EndElection()

# TODO move to channel_id.py
def channel_id_from_asset_name(encoded: str) -> ChannelId:
    channel_id = bytes.fromhex(encoded)
    assert ChannelIdHelper.validate_bytes(channel_id)
    LOG.debug(f'decoded {asset_name} -> {channel_id}')
    return channel_id

# TODO remove in favor of getting channel_ids from states?
# TODO where should this live?
def channel_id_from_output(output: UTxO) -> Optional[ChannelId]:
    for asset_key in output.value.assets.keys():
        policy_id, asset_name = asset_key.split('.')
        try:
            return channel_id_from_asset_name(asset_name)
        except:
            continue
    LOG.error(f'Output does not match any channel:\n{output}')
    return None

# TODO merge into Subscriber class?
def handle_match(utxo: Dict[str, Any], session: requests.Session) -> (ChannelId, ChannelState):
    LOG.debug(f'Full match UTxO:\n{json.dumps(utxo, indent=2)}')

    tx_id       = utxo.get('transaction_id')
    out_ix      = utxo.get('output_index')
    datum_hash  = utxo.get('datum_hash')
    datum_type  = utxo.get('datum_type')
    created     = utxo.get('created_at') or {}
    slot_no     = created.get('slot_no')
    header_hash = created.get('header_hash')

    assert datum_hash # TODO will this not exist in the final EndElection tx?

    try:
        datum = fetch_datum(session, datum_hash)

        # try subchannel first because that should be more common long term
        try:
            state = SubChannel(state=SubChannelState.from_cbor(datum['datum']))
            channel_id = state.state.channel_id
        except:
            state = AdminChannel(state=AdminChannelState.from_cbor(datum['datum']))
            channel_id = ADMIN_CHANNEL_ID

        LOG.debug(f'handle_match: decoded {channel_id} state {state.state.seq}: {state}')
        return (channel_id, state)

    except Exception as e:
        LOG.error(f'handle_match: failed to fetch datum {datum_hash}: {e}')
        raise

def kupo_to_utxo(kupo_dict: dict) -> UTxO:
    """Convert a Kupo UTXO response dict to a PyCardano UTxO.
    WARNING: Does not handle a lot of edge cases! Mainly for BurnTestTokens.
    """
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


class ElectionSubscriber:
    '''Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block_hash should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    '''

    def __init__(
            self,
            config: SubscriberConfig,
            # on_match: SubscriberCallback,
            # on_close: SubscriberCallback,
        ):

        LOG.debug('ElectionSubscriber.__init__')

        self.config = config

        # TODO does having these be separate functions help anymore?
        self.on_match = handle_match
        self.on_close = handle_endelection

        # used to reconstruct subscribed_records() on demand
        self.history: Mapping[ChannelId, Mapping[int, ChannelState]] = {}

        # used to query the current state
        # TODO can these both be put in the same map without making it annoying/fragile?
        self.states: Mapping[ChannelId, ChannelState] = {}

        # used to query raw utxos
        # TODO is this useful for anything other than burning?
        self.utxos: Mapping[ChannelId, UTxO] = {}

        # for managing the kupo process
        self._kupo_proc:   Optional[subprocess.Popen] = None
        self._kupo_thread: Optional[threading.Thread] = None
        self._kupo_stop = threading.Event()

        # to prevent duplicate processing of the same transactions
        self._seen_tx_ids: set[str] = set()

        # for http requests to the kupo process
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

        # we check whether this was spent without any new match to confirm a EndElection
        # TODO remove once state map works
        self._last_tx_key = None # TODO type?

    def __del__(self):
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

            '--log-level', 'Notice'

            # '--prune-utxo',

            # TODO is any margin needed in this case?
            # '--safety-margin', '100',

        ]

        LOG.info(f'Starting Kupo: {' '.join(cmd)}')
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
            LOG.info(f'Kupo output: {line}')
            if proc.poll() is not None:
                break
        # TODO why does this seem to happen immediately?
        LOG.info('Kupo subprocess output thread terminating')

    def stop_kupo(self) -> None:
        LOG.debug('ElectionSubscriber.stop_kupo')

        proc = self._kupo_proc
        if proc is None:
            return
        if proc.poll() is None:
            LOG.info(f'Terminating Kupo (pid={proc.pid})')
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

    def check_if_admin_channel_closed(self):
        LOG.debug('ElectionSubscriber.check_if_admin_channel_closed')
        if self._last_tx_key is None:
            LOG.debug('no transactions have been published yet?')
            return
        (tx_id, output_ix) = self._last_tx_key
        resp = self.session.get(KUPO_MATCHES_URL + f'/{output_ix}@{tx_id}') # TODO params? timeout?
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
                    self.on_close(utxo, self.session)
                    self.stop()
                    return
        LOG.debug(f'Channel not yet closed {resp}')

    def _watch_kupo(self) -> None:
        LOG.info(f'Watcher thread started for policy_id={self.config.policy_id}')

        while not self._kupo_stop.is_set():
            try:
                resp = self.session.get(
                    KUPO_MATCHES_URL,
                    timeout=10,
                    params={
                        'with_spent': 'false',
                        'order': 'oldest_first',
                    }
                )
                resp.raise_for_status()
                unspent_utxos = resp.json()

                if not isinstance(unspent_utxos, list):
                    raise Exception(f'Unexpected Kupo response type: {type(unspent_utxos)}')

                any_new_utxo = False

                for utxo_dict in unspent_utxos:
                    if not isinstance(utxo_dict, dict):
                        # continue
                        raise Exception(f'Unexpected utxo format {type(utxo_dict)}:\n{utxo_dict}')

                    # skip already-processed transactions
                    # TODO is this ever actually needed?
                    # TODO is this wrong in case of a roll-back?
                    tx_id = utxo_dict.get('transaction_id')
                    out_ix = utxo_dict.get('output_index')
                    key = (tx_id, out_ix)
                    if tx_id and key in self._seen_tx_ids:
                        continue
                    if tx_id:
                        # LOG.info(f'last_tx_key: {key}')
                        self._seen_tx_ids.add(key)
                        self._last_tx_key = key
                        any_new_utxo = True

                    try:

                        (channel_id, new_state) = self.on_match(utxo_dict, self.session)
                        LOG.debug(f'new_state: {new_state} ({type(new_state)})')

                        # assert isinstance(new_state, AdminChannelState), 'Each TX should have a AdminChannelState'
                        if not channel_id in self.history:
                            self.history[channel_id] = {}
                        self.history[channel_id][new_state.state.seq] = new_state

                        if not channel_id in self.states:
                            self.states[channel_id] = {}
                        self.states[channel_id] = new_state

                        if not channel_id in self.utxos:
                            self.utxos[channel_id] = {}
                        self.utxos[channel_id] = kupo_to_utxo(utxo_dict)

                    except Exception as e:
                        LOG.error(f'Error in self.on_match: {e}')

                if not any_new_utxo:
                    LOG.debug('No new UTXOs')
                    self.check_if_admin_channel_closed()
                    # TODO is this the only check like this? or do we need one per channel?

            except requests.RequestException as e:
                LOG.debug(f'Kupo polling error: {e}') # TODO back to warning?
                time.sleep(5)
            except Exception as e:
                LOG.error(f'Unexpected error in watcher: {e} {type(e)}')
                time.sleep(5)

            time.sleep(KUPO_POLL_SEC)

        LOG.info('Watcher thread exiting')

    def subscribed_records(self, channel_id: ChannelId):
        LOG.debug('ElectionSubscriber.subscribed_records')
        LOG.debug(f'history: {self.history}')
        records = []
        # TODO fix so even if one is missing, iteration doesn't get messed up
        if not channel_id in self.history:
            return []
        for seq in range(0, len(self.history[channel_id])):
            assert seq in self.history[channel_id], f'Missing records with channel_id={channel_id} seq={seq}.'
            records += list(self.history[channel_id][seq].state.new_records)
        return records

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
            LOG.info(f'Signal {sig} recieved, shutting down...')
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
        self.stop_kupo()
        self._kupo_stop.set()
        if self._kupo_thread and self._kupo_thread.is_alive():
            LOG.info('Waiting for watcher thread to exit...')
            try:
                self._kupo_thread.join(timeout=5)
            except Exception as e:
                if not 'cannot join current thread' in str(e):
                    raise
        self._kupo_thread = None

    def is_done(self):
        return self._kupo_stop.is_set() \
           and self._kupo_thread is None
