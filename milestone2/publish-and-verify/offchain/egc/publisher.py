"""Handles the shared low level details of publishing transactions.
Publishers are specialized to a particular keypair and channel,
which means they can automatically find and update the correct STT.
They publish TXs via Ogmios and files via IPFS (Kubo) (not Kupo).
"""

from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext, SigningKey, Transaction, TransactionBuilder, Value
from egc.ogmios import OGMIOS_CTX
# from egc.plutus import script as es
from egc import wallet as ew
from time import sleep
from typing import List, Optional
from egc.election import Election
from pprint import pformat
import logging
import time

LOG = logging.getLogger(__name__)

# from .ogmios import query_network_tip_sync
# from .wallet import addr_for_signing_key, vkh_for_signing_key
# from .plutus import (
#     pick_oneshot_utxo,
#     PubsubScript, PubsubAction, PsOpen, PsPublish, PsClose,
#     build_psopen_tx, build_pspublish_tx, build_psclose_tx
# )

# TODO refactor to take a Keypair object rather than 2 args?

class ElectionPublisher:

    # TODO pass kubo here and implement ipfs publishing
    def __init__(
        self,
        role: str,
        index: int,
        keys_dir: Path,
        # script: ElectionScript,
        election: Election,
        key_name: Optional[Path] = None,
        # TODO pass once using more than one: ogmios: OgmiosV6ChainContext,
        # TODO ipfs (kubo)
    ):
        """Create the publisher.
        """
        LOG.debug('ElectionPublisher.__init__')
        self.role = role
        self.index = index
        self.keys_dir = Path(keys_dir) # TODO ok if already a Path?
        self.election = election
        # self.script = script
        # self.ogmios = OGMIOS_CTX
        self.key_name = self.channel_id() if key_name is None else key_name
        self._init_keypair()
        # self.pubsub_script = PubsubScript(self.oneshot_utxo)
        # self.channel_state: Optional[str] = None # TODO formalize a type
        # self.published_cids = []
        # self.tip_before_open: Optional[tuple[int, str]] = None

    def _init_keypair(self):
        """Load the keypair, creating it first if needed."""
        LOG.debug('ElectionPublisher._init_keypair')
        self.keys_dir.mkdir(exist_ok=True)
        self.signing_key = ew.load_wallet_signing_key(keys_dir=self.keys_dir, name=self.key_name)
        self.verification_key_hash = ew.vkh_for_signing_key(self.signing_key)
        self.address = ew.addr_for_signing_key(self.signing_key)
        LOG.debug(f'signing key: {self.signing_key}')
        LOG.debug(f'verification key hash: {self.verification_key_hash}')
        LOG.debug(f'address: {self.address}')

    def channel_id(self) -> str:
        LOG.debug('ElectionPublisher.channel_id')
        if self.role == 'funder':
            # Funder doesn't have a channel and shouldn't need the id
            raise NotImplementedError
        elif self.role == 'admin':
            return self.role
        else:
            return f'{self.role}{self.index}'

    def sign_and_submit(self, txb: TransactionBuilder):
        LOG.debug('ElectionPublisher.sign_and_submit')

        # Check what the node actually sees
        utxos = OGMIOS_CTX.utxos(self.address)
        LOG.info('UTxOs at publisher address: %s' % len(utxos))
        for u in utxos:
            LOG.debug(
                '  %s#%d  (%d lovelace)' % (
                u.input.transaction_id, u.input.index, u.output.amount.coin
                if isinstance(u.output.amount, Value) else u.output.amount)
            )

        tx_signed = txb.build_and_sign(
            [self.signing_key],
            change_address=self.address
        )

        # Log the actual inputs in the built transaction
        LOG.debug('tx inputs:')
        for inp in tx_signed.transaction_body.inputs:
            LOG.debug('  %s#%d' % (inp.transaction_id, inp.index))

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.info(f'submitted tx with id={tx_signed.id}')

        return tx_signed

    # TODO get this working for the case where the utxo is confirmed + consumed between polls
    def wait_for_confirmation(self, tx: Transaction, max_seconds: int = 300, interval_seconds: int = 5):
        LOG.debug('ElectionPublisher.wait_for_confirmation')
        tx_id = str(tx.id) # TODO is this the right way?
        LOG.info(f'tx {tx_id} waiting up to {max_seconds} seconds for confirmation.')
        waited_seconds = 0
        while True:
            time.sleep(interval_seconds)
            waited_seconds += interval_seconds
            utxo = OGMIOS_CTX.utxo_by_tx_id(tx_id, 0)
            if utxo is None:
                if waited_seconds >= max_seconds:
                    msg = f'tx {tx_id} still not confirmed after {waited_seconds} seconds'
                    LOG.error(msg)
                    raise Exception(msg)
                continue
            else:
                LOG.info(f' confirmed after {waited_seconds} seconds')
                return
