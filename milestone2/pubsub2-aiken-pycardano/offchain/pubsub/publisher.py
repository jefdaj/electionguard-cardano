import time

from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext, SigningKey, Transaction
from typing import List

from .wallet import addr_for_signing_key, vkh_for_signing_key
from .plutus import (
    pick_oneshot_utxo,
    PubsubScript, PubsubAction, PsOpen, PsPublish, PsClose,
    build_psopen_tx, build_pspublish_tx, build_psclose_tx
)

class Publisher:

    def __init__(
        self,
        chain_context: OgmiosV6ChainContext,
        publisher_signing_key: SigningKey,
        # TODO ipfs_client
    ):
        self.chain_context = chain_context
        self.publisher_signing_key = publisher_signing_key
        self.publisher_verification_key_hash = vkh_for_signing_key(self.publisher_signing_key)
        self.publisher_address = addr_for_signing_key(self.publisher_signing_key)
        self.oneshot_utxo = pick_oneshot_utxo(chain_context, self.publisher_address)
        self.pubsub_script = PubsubScript(self.oneshot_utxo)
        self.channel_state: Optional[str] = None # TODO formalize a type
        self.published_cids = []

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

    def open_channel(self) -> Transaction:
        if self.channel_state is not None:
            raise Exception('open_channel requires no existing channel')
        tx = build_psopen_tx(
            self.chain_context,
            self.publisher_address,
            self.publisher_verification_key_hash,
            self.pubsub_script,
            self.oneshot_utxo,
        )
        tx = self.sign_and_submit(tx)
        self.channel_state = 'open'
        return tx

    def publish_cids(self, cids: List[bytes]) -> Transaction:
        if not self.channel_state in ['open', 'published']:
            raise Exception('publish_cids requires an open channel')
        tx = build_pspublish_tx(
            self.chain_context,
            self.pubsub_script,
            self.publisher_address,
            self.publisher_verification_key_hash,
            cids
        )
        tx = self.sign_and_submit(tx)
        self.channel_state = 'published'
        self.published_cids += cids
        return tx

    def close_channel(self) -> Transaction:
        if not self.channel_state in ['open', 'published']:
            raise Exception('close_channel requires an open channel')
        tx = build_psclose_tx(
            self.chain_context,
            self.publisher_address,
            self.publisher_verification_key_hash,
            self.pubsub_script,
        )
        tx = self.sign_and_submit(tx)
        self.channel_state = 'closed'
        return tx
