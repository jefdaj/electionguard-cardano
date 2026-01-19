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
SubscriberActionCallback = Callable[[dict, requests.Session], PubsubAction]

def fetch_datum(session: requests.Session, datum_hash: str) -> Any:
    url = f'http://{KUPO_HOST}:{KUPO_PORT}/v1/datums/{datum_hash}' # TODO global var?
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def handle_close(utxo: Dict[str, Any], session: requests.Session) -> PubsubAction:
    log_info('Channel closed')
    return PsClose()

def handle_match(utxo: Dict[str, Any], session: requests.Session) -> PubsubAction:
    '''
    `utxo` looks like the Kupo object you printed.
    For now, just log some key fields. Later you can:
      - fetch the datum by `datum_hash`
      - decode it to IPFS CIDs
      - pull from IPFS and store locally
    '''
    tx_id = utxo.get('transaction_id')
    out_ix = utxo.get('output_index')
    datum_hash = utxo.get('datum_hash')
    datum_type = utxo.get('datum_type')
    created = utxo.get('created_at') or {}
    slot_no = created.get('slot_no')
    header_hash = created.get('header_hash')

    # log_info(
    #     'UTxO: tx_id={}#{} slot={} header_hash={} datum_type={} datum_hash={}',
    #     tx_id,
    #     out_ix,
    #     slot_no,
    #     header_hash,
    #     datum_type,
    #     datum_hash,
    # )

    # For debugging, print the full object:
    # dbg = json.dumps(utxo, indent=2)
    # log_info('Full UTxO:\n{}', dbg)

    if not datum_hash:
        # TODO what if this appears out of order?
        # should be PsClose
        # TODO is there a better way to check that?
        log_info('Hit PsClose')
        log_info('Full UTxO:\n{}', dbg)
        return None # TODO better stop signal?

    else:
        # PsOpen or PsPublish, both of which should have CID lists (PsOpen's is empty)
        try:
            datum = fetch_datum(session, datum_hash)
            # log_info('Fetched datum for {}: {}', datum_hash, json.dumps(datum, indent=2))

            state = PubsubState.from_cbor(datum['datum'])
            # log_info(f'Decoded datum to {type(state)}')
            log_info(f'Decoded state {state.seq} ({len(state.cids)} new CIDs)')
            return state

            # Later: decode IPFS CIDs from `datum` here.
        except Exception as e:
            log_error('Failed to fetch datum {}: {}', datum_hash, e)
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
            on_match: SubscriberActionCallback,
            on_close: SubscriberActionCallback,
        ):

        self.config = config
        self.on_match = on_match
        self.on_close = on_close
        self.cids_by_seq: Mapping[int, List[bytes]] = {}

        self._kupo_proc: Optional[subprocess.Popen] = None
        self._watcher_thread: Optional[threading.Thread] = None
        self._watcher_stop = threading.Event()
        self._seen_tx_ids: set[str] = set()

        # We check whether this was spent without any new match to confirm a PsClose.
        self._last_tx_key = None # TODO type?

        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})


    def start_kupo_if_needed(self) -> None:
        '''
        Start Kupo as a subprocess if it's not already running.
        Uses `--since {slot}.{hash}` and `--match '{policy_id}/*'`.
        '''
        # global _kupo_proc

        if self._kupo_proc is not None and self._kupo_proc.poll() is None:
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

        log_info('Starting Kupo: {}', ' '.join(cmd))
        self._kupo_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Log Kupo output in a helper thread
        threading.Thread(
            target=self._log_kupo_output,
            args=(),
            daemon=True,
        ).start()

    def _log_kupo_output(self) -> None:
        proc = self._kupo_proc
        if proc.stdout is None:
            return
        for line in proc.stdout:
            line = line.rstrip('\n')
            if not line:
                continue
            log_info('[KUPO] {}', line)
            if proc.poll() is not None:
                break
        # TODO why does this seem to happen immediately?
        log_info('Kupo subprocess output thread terminating')

    def stop_kupo(self) -> None:
        proc = self._kupo_proc
        if proc is None:
            return
        if proc.poll() is None:
            log_info('Terminating Kupo (pid={})', proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                log_warn('Kupo did not exit in time, killing...')
                proc.kill()
        self._kupo_proc = None

    def check_if_channel_closed(self):
        # log_info('check_if_channel_closed')
        (tx_id, output_ix) = self._last_tx_key
        resp = self.session.get(KUPO_MATCHES_URL + f'/{output_ix}@{tx_id}') # TODO params? timeout?
        if resp.status_code == 200:
            utxos = resp.json()
            # log_info('utxos type: {}', type(utxos))
            # log_info('utxos: {}', utxos)
            assert isinstance(utxos, list), "expected a list of UTXOs"
            for utxo in utxos:
                # There should only be one
                # log_info(f'utxo: {type(utxo)}')
                # log_info(f'utxo keys: {utxo.keys()}')
                if 'spent_at' in utxo:
                    # Confirmed spent
                    # log_info(f'spent_at: {utxo['spent_at']}')
                    self.on_close(utxo, self.session)
                    self.stop()
                    return
        # log_info(f'Probably not closed? {resp}')

    def _watch_kupo(self) -> None:
        log_info('Watcher thread started for policy_id={}', self.config.policy_id)

        while not self._watcher_stop.is_set():
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
                    raise Exception(f'Unexpected Kupo response type: {type(unspent_utxos)}')
                    # time.sleep(KUPO_POLL_SEC)
                    # continue

                # pprint(f'unspent_utxos: {unspent_utxos}')
                # print(flush=True)

                any_new_utxo = False

                for utxo in unspent_utxos:
                    if not isinstance(utxo, dict):
                        # continue
                        raise Exception(f'Unexpected utxo format {type(utxo)}:\n{utxo}')

                    # skip already-processed transactions
                    # TODO is this ever actually needed?
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
                        if len(new_state.cids) > 0:
                            self.cids_by_seq[new_state.seq] = new_state.cids

                    except Exception as e:
                        log_error('Error in self.on_match: {}', e)

                if not any_new_utxo:
                    self.check_if_channel_closed()

            except requests.RequestException as e:
                log_warn('Kupo polling error: {}', e)
                time.sleep(5)
            except Exception as e:
                log_error('Unexpected error in watcher: {} {}', e, type(e))
                time.sleep(5)

            time.sleep(KUPO_POLL_SEC)

        log_info('Watcher thread exiting')

    # TODO exception if there's a missing seq?
    def subscribed_cids(self):
        cids = []
        for seq in sorted(self.cids_by_seq.keys()):
            cids += self.cids_by_seq[seq]
        return cids

    def start(self) -> None:
        self._watcher_stop.clear()

        def _start_and_watch() -> None:
            try:
                self.start_kupo_if_needed()
                self._watch_kupo()
            except Exception as e:
                log_error('Error in watcher: {}', e)

        self._watcher_thread = threading.Thread(
            target=_start_and_watch,
            daemon=True,
        )
        self._watcher_thread.start()

    def join(self):
        # TODO is this how this works?
        self._watcher_thread.join(timeout=5)

    def stop(self) -> None:
        self.stop_kupo()
        self._watcher_stop.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            log_info('Waiting for watcher thread to exit...')
            try:
                self._watcher_thread.join(timeout=5)
            except Exception as e:
                if not 'cannot join current thread' in str(e):
                    raise
        self._watcher_thread = None
