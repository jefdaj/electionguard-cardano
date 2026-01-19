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

from dataclasses import dataclass
from os import environ
from pprint import pprint
from pycardano import *
from typing import Any, Callable, Dict, List, Optional

from .ogmios import OGMIOS_HOST, OGMIOS_PORT
from .plutus import PubsubState, PubsubAction, PsOpen, PsPublish, PsClose

KUPO_HOST = environ.get('KUPO_HOST', '127.0.0.1')
KUPO_PORT = int(environ.get('KUPO_PORT', '1442'))
KUPO_MATCHES_URL = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/matches'
KUPO_POLL_SEC = 2.0

NODE_SOCKET = environ.get('CARDANO_NODE_SOCKET_PATH', '../../cardano-node-ogmios/data/node-ipc/node.socket')
NODE_CONFIG = environ.get('NODE_CONFIG', '../../cardano-node-ogmios/config/network/preview/cardano-node/config.json')

# TODO remove?
def log_info(msg: str, *args: Any) -> None:
    print('[INFO] ' + msg.format(*args), file=sys.stderr, flush=True)

# TODO remove?
def log_warn(msg: str, *args: Any) -> None:
    print('[WARN] ' + msg.format(*args), file=sys.stderr, flush=True)

# TODO remove?
def log_error(msg: str, *args: Any) -> None:
    print('[ERROR] ' + msg.format(*args), file=sys.stderr, flush=True)

@dataclass
class SubscriberConfig:
    since_slot: int  # For kupo --since
    since_block: str # For kupo --since
    policy_id: str # For kupo --match TODO remove?
    until_slot: Optional[int] = None # For kupo --until, to prevent open-ended scans during tests

# Handles a single kupo match response json obj.
# I think kupo yields an iterator of these? TODO check that
# TODO can the response type be more specific than dict?
SubscriberCallback = Callable[[dict, requests.Session], PubsubAction]

def fetch_datum(session: requests.Session, datum_hash: str) -> Any:
    url = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/datums/{datum_hash}' # TODO global var?
    log_info('[match] fetching datum {}', datum_hash)
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def handle_close(utxo: Dict[str, Any], session: requests.Session) -> PubsubAction:
    log_info('[close] Channel closed')
    return PsClose()

def handle_match(utxo: Dict[str, Any], session: requests.Session) -> PubsubAction:
    tx_id = utxo.get('transaction_id')
    out_ix = utxo.get('output_index')
    datum_hash = utxo.get('datum_hash')
    datum_type = utxo.get('datum_type')
    created = utxo.get('created_at') or {}
    slot_no = created.get('slot_no')
    header_hash = created.get('header_hash')

    # dbg = json.dumps(utxo, indent=2)
    # log_info('Full UTxO:\n{}', dbg)

    assert datum_hash

    try:
        datum = fetch_datum(session, datum_hash)
        state = PubsubState.from_cbor(datum['datum'])
        log_info(f'[match] Decoded state {state.seq} with {len(state.cids)} new CIDs')
        return state

    except Exception as e:
        log_error('[match] Failed to fetch datum {}: {}', datum_hash, e)
        raise

class Subscriber:
    '''
    Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    '''

    def __init__(
            self,
            config: SubscriberConfig,
            on_match: SubscriberCallback,
            on_close: SubscriberCallback,
        ):

        log_info('[sub] init')

        self.config = config
        self.on_match = on_match
        self.on_close = on_close

        # used to reconstruct subscribed_cids() on demand
        self.cids_by_seq: Mapping[int, List[bytes]] = {}

        # for managing the kupo process
        self._kupo_proc:   Optional[subprocess.Popen] = None
        self._kupo_thread: Optional[threading.Thread] = None
        self._kupo_stop = threading.Event()

        # to prevent duplicate processing of the same transactions
        self._seen_tx_ids: set[str] = set()

        # for http requests to the kupo process
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})

        # we check whether this was spent without any new match to confirm a PsClose
        self._last_tx_key = None # TODO type?


    def _start_kupo(self) -> None:
        '''
        Start Kupo as a subprocess.
        Uses `--since {slot}.{hash}` and `--match '{policy_id}/*'`.
        '''
        log_info('[sub] _start_kupo')

        if self._kupo_proc is not None and self._kupo_proc.poll() is None:
            # TODO error here?
            log_info('Kupo already running (pid={})', self._kupo_proc.pid)
            return

        # os.makedirs(KUPO_WORKDIR, exist_ok=True)
        since_arg = f'{self.config.since_slot}.{self.config.since_block}'

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

        log_info('[sub] Starting Kupo: {}', ' '.join(cmd))
        self._kupo_proc = subprocess.Popen(
            cmd,
            preexec_fn=os.setsid, # makes handling signals more reliable
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Log Kupo output in a helper thread
        # TODO does this really need a separate thread?
        threading.Thread(
            target=self._log_kupo_output,
            args=(),
            daemon=True,
        ).start()

        time.sleep(0.1) # prevents polling error during startup

    def _log_kupo_output(self) -> None:
        log_info('[sub] _log_kupo_output')
        proc = self._kupo_proc
        if proc.stdout is None:
            return
        for line in proc.stdout:
            line = line.rstrip('\n')
            if not line:
                continue
            log_info('[kupo] {}', line)
            if proc.poll() is not None:
                break
        # TODO why does this seem to happen immediately?
        log_info('[sub] Kupo subprocess output thread terminating')

    def stop_kupo(self) -> None:
        log_info('[sub] stop_kupo')
        proc = self._kupo_proc
        if proc is None:
            return
        if proc.poll() is None:
            log_info('[sub] Terminating Kupo (pid={})', proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log_warn('[sub] Kupo did not exit in time, killing...')
                proc.kill()
                proc.wait() # TODO remove?
        self._kupo_proc = None

    def check_if_channel_closed(self):
        log_info('[sub] check_if_channel_closed')
        (tx_id, output_ix) = self._last_tx_key
        resp = self.session.get(KUPO_MATCHES_URL + f'/{output_ix}@{tx_id}') # TODO params? timeout?
        if resp.status_code == 200:
            utxos = resp.json()
            assert isinstance(utxos, list), "expected a list of UTXOs"
            for utxo in utxos:
                # There should only be one
                if 'spent_at' in utxo:
                    # Confirmed spent
                    log_info(f'[sub] STT UTXO spent without creating a new one')
                    # for some reason, actually printing spent_at here produces errors
                    self.on_close(utxo, self.session)
                    self.stop()
                    return
        log_info(f'[sub] channel not yet closed {resp}')

    def _watch_kupo(self) -> None:
        log_info('[sub] Watcher thread started for policy_id={}', self.config.policy_id)

        while not self._kupo_stop.is_set():
            try:
                resp = self.session.get(
                    KUPO_MATCHES_URL,
                    timeout=10,
                    params={
                        'with_spent': 'false',
                        'order': 'oldest_first',
                        # TODO resolve_datums?
                    }
                )
                resp.raise_for_status()
                unspent_utxos = resp.json()

                if not isinstance(unspent_utxos, list):
                    raise Exception(f'[sub] Unexpected Kupo response type: {type(unspent_utxos)}')

                any_new_utxo = False

                for utxo in unspent_utxos:
                    if not isinstance(utxo, dict):
                        # continue
                        raise Exception(f'[sub] Unexpected utxo format {type(utxo)}:\n{utxo}')

                    # skip already-processed transactions
                    # TODO is this ever actually needed?
                    # TODO is this wrong in case of a roll-back?
                    tx_id = utxo.get('transaction_id')
                    out_ix = utxo.get('output_index')
                    key = (tx_id, out_ix)
                    if tx_id and key in self._seen_tx_ids:
                        continue
                    if tx_id:
                        # log_info(f'last_tx_key: {key}')
                        self._seen_tx_ids.add(key)
                        self._last_tx_key = key
                        any_new_utxo = True

                    try:

                        new_state = self.on_match(utxo, self.session)
                        # log_info(f'new_state: {new_state} ({type(new_state)})')

                        assert isinstance(new_state, PubsubState), 'Each TX should have a PubsubState'
                        self.cids_by_seq[new_state.seq] = new_state.cids

                    except Exception as e:
                        log_error('[sub] Error in self.on_match: {}', e)

                if not any_new_utxo:
                    self.check_if_channel_closed()

            except requests.RequestException as e:
                log_warn('[sub] Kupo polling error: {}', e)
                time.sleep(5)
            except Exception as e:
                log_error('[sub] Unexpected error in watcher: {} {}', e, type(e))
                time.sleep(5)

            time.sleep(KUPO_POLL_SEC)

        log_info('[sub] Watcher thread exiting')

    def subscribed_cids(self):
        cids = []
        for seq in range(0, len(self.cids_by_seq)):
            assert seq in self.cids_by_seq, f'Missing CID batch {seq}'
            cids += self.cids_by_seq[seq]
        return cids

    def start(self) -> None:
        log_info('[sub] start')
        self._kupo_stop.clear()

        def _start_and_watch() -> None:
            try:
                self._start_kupo()
                self._watch_kupo()
            except Exception as e:
                log_error('Error in watcher: {}', e)

        def handle_sigint(sig, frame):
            log_info('[sigint] signal {} recieved, shutting down...', sig)
            self.stop()

        signal.signal(signal.SIGINT , handle_sigint)
        signal.signal(signal.SIGTERM, handle_sigint)

        self._kupo_thread = threading.Thread(
            target=_start_and_watch,
            daemon=False,
        )
        self._kupo_thread.start()

    def join(self):
        log_info('[sub] join')
        # TODO how is this actually supposed to be done?
        while not self.is_done():
            time.sleep(1)

    def stop(self) -> None:
        log_info('[sub] stop')
        self.stop_kupo()
        self._kupo_stop.set()
        if self._kupo_thread and self._kupo_thread.is_alive():
            log_info('[sub] Waiting for watcher thread to exit...')
            try:
                self._kupo_thread.join(timeout=5)
            except Exception as e:
                if not 'cannot join current thread' in str(e):
                    raise
        self._kupo_thread = None

    def is_done(self):
        return self._kupo_stop.is_set() \
           and self._kupo_thread is None
