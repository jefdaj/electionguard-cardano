import time

from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext, SigningKey, Transaction

from .builders import build_psopen_tx
from .types import PubsubAction, PsOpen, PsClose
from .utils import addr_for_signing_key, pick_oneshot_utxo
from .script import PubsubScript

class PubsubClient:

    def __init__(
        self,
        chain_context: OgmiosV6ChainContext,
        raw_plutus_json_path: Path, # TODO where to load this from?
        publisher_signing_key: SigningKey,
        # TODO ipfs_client
    ):
        self.chain_context = chain_context
        self.publisher_signing_key = publisher_signing_key
        self.publisher_address = addr_for_signing_key(self.publisher_signing_key)
        self.oneshot_utxo = pick_oneshot_utxo(chain_context, self.publisher_address)
        self.pubsub_script = PubsubScript(raw_plutus_json_path, self.oneshot_utxo)

    def sign_and_submit(self, tx: Transaction):
        tx_signed = tx.build_and_sign(
            [self.publisher_signing_key],
            change_address=self.publisher_address
        )
        self.chain_context.submit_tx(tx_signed)
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
            utxo = self.chain_context.utxo_by_tx_id(tx_id, 0)
            if utxo is None:
                if waited_seconds >= max_seconds:
                    print(' FAIL', flush=True)
                    raise Exception(f'tx {tx_id} still not confirmed after {waited_seconds} seconds')
                continue
            else:
                print(f' confirmed after {waited_seconds} seconds', flush=True)
                return

    def open_channel(self):
        # TODO prevent if already open?
        tx = build_psopen_tx(
            self.chain_context,
            self.publisher_address,
            self.pubsub_script,
            self.oneshot_utxo,
        )
        self.sign_and_submit(tx)
        # TODO return anything?

    def close_channel(self):
        # TODO prevent if already closed?
        tx = build_psclose(
            self.chain_context,
            self.publisher_address,
            self.pubsub_script,
        )
        self.sign_and_submit(tx)
        # TODO return anything?
