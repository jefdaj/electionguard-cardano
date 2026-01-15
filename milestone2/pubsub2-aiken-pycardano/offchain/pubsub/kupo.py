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

from dataclass import dataclass
from os import environ
from pprint import pprint
from typing import Any, Callable, Dict, List, Optional

from .ogmios import OGMIOS_HOST, OGMIOS_PORT


KUPO_HOST = environ.get("KUPO_HOST", "127.0.0.1")
KUPO_PORT = int(environ.get("KUPO_PORT", "1442"))
KUPO_MATCHES_URL = f"http://{KUPO_HOST}:{KUPO_PORT}/v1/matches"
KUPO_POLL_SEC = 2.0


# not needed with --in-memory
# KUPO_WORKDIR = os.environ.get("KUPO_WORKDIR", "../data/kupo")

NODE_SOCKET = environ.get("CARDANO_NODE_SOCKET_PATH", "../../cardano-node-ogmios/data/node-ipc/node.socket")
NODE_CONFIG = environ.get("NODE_CONFIG", "../../cardano-node-ogmios/config/network/preview/cardano-node/config.json")

# imported from ogmios.py instead
# OGMIOS_HOST = os.environ.get("OGMIOS_HOST", "localhost")
# OGMIOS_PORT = int(os.environ.get("OGMIOS_PORT", "1337"))


def log_info(msg: str, *args: Any) -> None:
    print("[INFO] " + msg.format(*args), file=sys.stderr, flush=True)


def log_warn(msg: str, *args: Any) -> None:
    print("[WARN] " + msg.format(*args), file=sys.stderr, flush=True)


def log_error(msg: str, *args: Any) -> None:
    print("[ERROR] " + msg.format(*args), file=sys.stderr, flush=True)


@dataclass
class KupoConfig:
    since_slot: int  # For kupo --since
    since_block: str # For kupo --since
    until_slot: Optional[int] # For kupo --until, to prevent open-ended scans during tests
    policy_id: str # For kupo --match TODO remove?


# TODO is this how you define a type?
# TODO can the response type be more specific than dict?
# Handles a single kupo match response json obj.
# I think kupo yields an iterator of these? TODO check that
KupoMatchCallback = Callable[[dict], None]


def fetch_datum(session: requests.Session, datum_hash: str) -> Any:
    url = f"http://{KUPO_HOST}:{KUPO_PORT}/v1/datums/{datum_hash}" # TODO global var?
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def handle_match(utxo: Dict[str, Any], session: requests.Session) -> None:
    """
    `utxo` looks like the Kupo object you printed.
    For now, just log some key fields. Later you can:
      - fetch the datum by `datum_hash`
      - decode it to IPFS CIDs
      - pull from IPFS and store locally
    """
    tx_id = utxo.get("transaction_id")
    out_ix = utxo.get("output_index")
    datum_hash = utxo.get("datum_hash")
    datum_type = utxo.get("datum_type")
    created = utxo.get("created_at") or {}
    slot_no = created.get("slot_no")
    header_hash = created.get("header_hash")

    log_info(
        "UTxO: tx_id={}#{} slot={} header_hash={} datum_type={} datum_hash={}",
        tx_id,
        out_ix,
        slot_no,
        header_hash,
        datum_type,
        datum_hash,
    )

    # For debugging, print the full object:
    dbg = json.dumps(utxo, indent=2)
    log_info("Full UTxO:\n{}", dbg)

    if datum_hash:
        try:
            datum = fetch_datum(session, datum_hash)
            log_info("Fetched datum for {}: {}", datum_hash, json.dumps(datum, indent=2))
            # Later: decode IPFS CIDs from `datum` here.
        except Exception as e:
            log_error("Failed to fetch datum {}: {}", datum_hash, e)


class KupoSubscriberThread:
    """
    Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    """

    def __init__(
            self,
            config: KupoConfig,
            on_match: KupoMatchCallback
        ):

        self.config = config
        self.on_match = on_match

        self._kupo_proc: Optional[subprocess.Popen] = None
        self._watcher_thread: Optional[threading.Thread] = None
        self._watcher_stop = threading.Event()
        self._seen_tx_ids: set[str] = set()


    # def start_kupo_if_needed(policy_id: str, start_slot: int, block_hash: str) -> None:
    def start_kupo_if_needed(self) -> None:
        """
        Start Kupo as a subprocess if it's not already running.
        Uses `--since {slot}.{hash}` and `--match '{policy_id}/*'`.
        """
        # global _kupo_proc

        if self._kupo_proc is not None and self._kupo_proc.poll() is None:
            log_info("Kupo already running (pid={})", self._kupo_proc.pid)
            return

        # os.makedirs(KUPO_WORKDIR, exist_ok=True)
        since_arg = f"{self.config.since_slot}.{self.config._since_block}"

        cmd = [

            "kupo",

            "--ogmios-host", OGMIOS_HOST,
            "--ogmios-port", str(OGMIOS_PORT),

            # at least for development, in memory should be fine
            # "--workdir", KUPO_WORKDIR,
            "--in-memory",

            "--since", since_arg,
            "--match", f"{self.config.policy_id}/*",

            "--host", KUPO_HOST,
            "--port", str(KUPO_PORT),

            # "--prune-utxo",

            # TODO is any margin needed in this case?
            # "--safety-margin", "100",

        ]

        log_info("Starting Kupo: {}", " ".join(cmd))
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
            # args=(self._kupo_proc,),
            args=(),
            daemon=True,
        ).start()

    # def _log_kupo_output(proc: subprocess.Popen) -> None:
    def _log_kupo_output(self) -> None:
        proc = self._kupo_proc
        if proc.stdout is None:
            return
        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue
            log_info("[KUPO] {}", line)
            if proc.poll() is not None:
                break
        log_info("Kupo subprocess output thread terminating")


    def stop_kupo(self) -> None:
        proc = self._kupo_proc
        # global _kupo_proc
        if proc is None:
            return
        if proc.poll() is None:
            log_info("Terminating Kupo (pid={})", proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                log_warn("Kupo did not exit in time, killing...")
                proc.kill()
        self._kupo_proc = None


    # def _watch_kupo(policy_id: str) -> None:
    def _watch_kupo(self) -> None:
        policy_id = self.config.policy_id
        log_info("Watcher thread started for policy_id={}", policy_id)

        session = requests.Session() # TODO store in self?
        session.headers.update({"Accept": "application/json"})

        while not self._watcher_stop.is_set():
            try:
                resp = session.get(KUPO_MATCHES_URL), timeout=10)
                resp.raise_for_status()
                data = resp.json()

                # Your Kupo: `data` is a plain list of UTxOs.
                if not isinstance(data, list):
                    log_warn("Unexpected Kupo response type: {}", type(data))
                    time.sleep(KUPO_POLL_SEC)
                    continue

                for utxo in data:
                    if not isinstance(utxo, dict):
                        continue

                    tx_id = utxo.get("transaction_id")
                    out_ix = utxo.get("output_index")

                    # Use (tx_id, out_ix) as unique key
                    key = (tx_id, out_ix)
                    if tx_id and key in _seen_tx_ids:
                        continue
                    if tx_id:
                        _seen_tx_ids.add(key)

                    try:
                        # handle_match(utxo, session)
                        self.on_match(utxo, session)
                    except Exception as e:
                        log_error("Error in self.on_match: {}", e)

            except requests.RequestException as e:
                log_warn("Kupo polling error: {}", e)
                time.sleep(5)
            except Exception as e:
                log_error("Unexpected error in watcher: {}", e)
                time.sleep(5)

            time.sleep(KUPO_POLL_SEC)

        log_info("Watcher thread exiting")


    # def start_watcher(policy_id: str, start_slot: int, block_hash: str) -> None:
    def start_watcher(self) -> None:
        # global _watcher_thread
        self._watcher_stop.clear()

        def _start_and_watch() -> None:
            try:
                # start_kupo_if_needed(policy_id, start_slot, block_hash)
                # self._watch_kupo(policy_id)
                self.start_kupo_if_needed()
                self._watch_kupo()
            except Exception as e:
                log_error("Error in watcher: {}", e)

        self._watcher_thread = threading.Thread(
            target=_start_and_watch,
            daemon=True,
        )
        self._watcher_thread.start()


    def stop_watcher(self) -> None:
        # global _watcher_thread
        self._watcher_stop.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            log_info("Waiting for watcher thread to exit...")
            self._watcher_thread.join(timeout=5)
        self._watcher_thread = None


# ------------------ CLI + main ------------------

# def parse_args() -> argparse.Namespace:
#     parser = argparse.ArgumentParser(
#         description="Simple Kupo-based subscriber for a policy ID."
#     )
#     parser.add_argument("--policy-id", required=True, help="Policy ID (hex)")
#     parser.add_argument("--start-slot", type=int, required=True, help="Start slot")
#     parser.add_argument("--block-hash", required=True, help="Block hash (hex)")
#     return parser.parse_args()


# def main() -> None:
#     args = parse_args()
# 
#     log_info("Starting subscriber with policy_id={}, since {}.{}",
#              args.policy_id, args.start_slot, args.block_hash)
# 
#     def handle_sigint(sig, frame):
#         log_info("Signal {} received, shutting down...", sig)
#         stop_watcher()
#         stop_kupo()
#         sys.exit(0)
# 
#     signal.signal(signal.SIGINT, handle_sigint)
#     signal.signal(signal.SIGTERM, handle_sigint)
# 
#     start_watcher(args.policy_id, args.start_slot, args.block_hash)
# 
#     # Just sleep until interrupted
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         handle_sigint(signal.SIGINT, None)


if __name__ == "__main__":
    main()
