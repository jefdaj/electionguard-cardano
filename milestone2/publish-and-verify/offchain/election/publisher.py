"""Handles the shared low level details of publishing transactions.
Publishers are specialized to a particular keypair and channel,
which means they can automatically find and update the correct STT.
They publish TXs via Ogmios and files via IPFS (Kubo) (not Kupo).
"""

from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext, SigningKey, Transaction, TransactionBuilder
from time import sleep
from typing import List, Optional

# from .ogmios import query_network_tip_sync
# from .wallet import addr_for_signing_key, vkh_for_signing_key
# from .plutus import (
#     pick_oneshot_utxo,
#     PubsubScript, PubsubAction, PsOpen, PsPublish, PsClose,
#     build_psopen_tx, build_pspublish_tx, build_psclose_tx
# )

class ElectionPublisher:

    # TODO pass kubo here and implement ipfs publishing
    def __init__(
        self,
        role: str,
        index: int,
        keys_dir: Path,
        script: ElectionScript,
        ogmios: OgmiosV6ChainContext,
        # TODO ipfs (kubo)
    ):
        """Create the publisher.
        The script should already have been parameterized with a one-shot UTxO by the Admin.
        """
        self.role = role
        self.index = index
        self.keys_dir = keys_dir
        self.ogmios = ogmios
        self.script = script
        self._init_keypair()
        # self.publisher_address = addr_for_signing_key(self.publisher_signing_key)
        # self.oneshot_utxo = pick_oneshot_utxo(ogmios, self.publisher_address)
        # self.pubsub_script = PubsubScript(self.oneshot_utxo)
        # self.channel_state: Optional[str] = None # TODO formalize a type
        # self.published_cids = []
        # self.tip_before_open: Optional[tuple[int, str]] = None

    def _init_keypair(self):
        """Load the keypair, creating it first if needed."""
        self.keys_dir.mkdir(exist_ok=True)
        name = self.channel_id()
        sk_path   = self.keys_dir / (name + '.sk')
        addr_path = self.keys_dir / (name + '.addr')
        if not sk_path.exists():
            pass
        # self.publisher_signing_key = publisher_signing_key
        # self.publisher_verification_key_hash = vkh_for_signing_key(self.publisher_signing_key)

    def channel_id(self) -> str:
        return 'admin' if self.role == 'admin' else f'{self.role}{self.index}'

    def sign_and_submit(self, txb: TransactionBuilder):
        tx_signed = txb.build_and_sign(
            [self.publisher_signing_key],
            change_address=self.publisher_address
        )
        self.ogmios.submit_tx(tx_signed)
        print(f'submitted tx with id={tx_signed.id}')
        return tx_signed

    # TODO get this working for the case where the utxo is confirmed + consumed between polls
    def wait_for_confirmation(self, tx: Transaction, max_seconds: int = 300, interval_seconds: int = 5):
        tx_id = str(tx.id) # TODO is this the right way?
        print(f'tx {tx_id} waiting up to {max_seconds} seconds for confirmation', end='', flush=True)
        waited_seconds = 0
        while True:
            time.sleep(interval_seconds)
            waited_seconds += interval_seconds
            print('.', end='', flush=True)
            utxo = self.ogmios.utxo_by_tx_id(tx_id, 0)
            if utxo is None:
                if waited_seconds >= max_seconds:
                    print(' FAIL', flush=True)
                    raise Exception(f'tx {tx_id} still not confirmed after {waited_seconds} seconds')
                continue
            else:
                print(f' confirmed after {waited_seconds} seconds', flush=True)
                return
