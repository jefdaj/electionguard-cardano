"""Handles the shared low level details of publishing transactions.
Publishers are specialized to a particular keypair and channel,
which means they can automatically find and update the correct STT.
They publish TXs via Ogmios and files via IPFS (Kubo) (not Kupo).
"""

from pathlib import Path
from time import sleep
from typing import List, Optional
from pprint import pformat
import logging
import time

LOG = logging.getLogger(__name__)

from .ogmios   import OGMIOS_CTX
from .election import ElectionContext
from .wallet   import *
from .plutus   import ChannelId, ChannelIdHelper

from pycardano import *

class ElectionPublisher:

    def __init__(
        self,

        # Election role and index: "guardian1", "verifier2" etc.
        # Funders and Admins don't need the index.
        # TODO restrict it to 1 in those cases?
        role: str,
        role_index: int,

        # No need for keys_dir or key_name if you pass an existing key_pair.
        # You can also omit them without passing key_pair, in which case a new
        # KeyPair will generated based on the role + index and saved in the
        # default dir.
        key_pair: Optional[KeyPair] = None,
        keys_dir: Optional[Path]    = None,
        key_name: Optional[Path]    = None,

        # If the script is not given here, you have to call _init_script()
        # separately. That's expected when creating a Funder (and possibly
        # Admin), because the script won't exist yet at that point. If the
        # script is available, you should use it.
        # TODO wait, can this be done without the script at all?
        # script: Optional[ElectionScript],

        # TODO ipfs (kubo) url for publishing files

    ):
        """Create the publisher.
        """
        LOG.debug('ElectionPublisher.__init__')

        self.role = role
        self.role_index = role_index

        if key_pair is None:
            LOG.debug('key_pair is None; create new KeyPair')
            if keys_dir is None:
                keys_dir = DEF_KEYS_DIR
                LOG.debug(f'keys_dir is None; default to {keys_dir}')
            keys_dir = Path(keys_dir) # TODO ok if already a Path?
            if key_name is None:
                key_name = ChannelIdHelper.to_string(self.channel_id())
                LOG.debug(f'key_name is None; default to {key_name}')
            self.key_pair = KeyPair(keys_dir=keys_dir, name=key_name, verbose=False)
        else:
            LOG.debug(f'use existing key_pair {key_pair}')
            self.key_pair = key_pair

        # TODO what did this need the election for?
        # self.election = election

        # self.script = script

        # self.ogmios = OGMIOS_CTX
        # self.pubsub_script = PubsubScript(self.oneshot_utxo)
        # self.channel_state: Optional[str] = None # TODO formalize a type
        # self.published_cids = []
        # self.tip_before_open: Optional[tuple[int, str]] = None

    # def _init_keypair(self):
    #     """Load the keypair, creating it first if needed."""
    #     LOG.debug('ElectionPublisher._init_keypair')
    #     self.keys_dir.mkdir(exist_ok=True)
    #     self.key_pair.sk = load_wallet_signing_key(keys_dir=self.keys_dir, name=self.key_name)
    #     self.verification_key_hash = vkh_for_signing_key(self.key_pair.sk)
    #     self.key_pair.addr = addr_for_signing_key(self.key_pair.sk)
    #     LOG.debug(f'signing key: {self.key_pair.sk}')
    #     LOG.debug(f'verification key hash: {self.verification_key_hash}')
    #     LOG.debug(f'address: {self.key_pair.addr}')

    # TODO remove?
    # def set_script(self, script: ElectionScript):
    #     LOG.debug('ElectionPublisher.set_script')
    #     if self.script is not None:
    #         raise Exception(f'script already set to {self.script}')
    #     self.script = script

    def channel_id(self) -> ChannelId:
        LOG.debug('ElectionPublisher.channel_id')
        if self.role in ['funder', 'admin']:
            # TODO is there ever a need for the Funder's "channel_id", since there's no channel?
            channel_str = self.role
        else:
            channel_str = f'{self.role}{self.role_index}'
        return ChannelIdHelper.from_string(channel_str)

    def sign_and_submit(self, txb: TransactionBuilder):
        LOG.debug('ElectionPublisher.sign_and_submit')

        # Check what the node actually sees
        utxos = OGMIOS_CTX.utxos(self.key_pair.addr)
        LOG.info('UTxOs at publisher address: %s' % len(utxos))
        for u in utxos:
            LOG.debug(
                '  %s#%d  (%d lovelace)' % (
                u.input.transaction_id, u.input.index, u.output.amount.coin
                if isinstance(u.output.amount, Value) else u.output.amount)
            )

        tx_signed = txb.build_and_sign(
            [self.key_pair.sk],
            change_address=self.key_pair.addr
        )

        # Log the actual inputs in the built transaction
        LOG.debug('tx inputs:')
        for inp in tx_signed.transaction_body.inputs:
            LOG.debug('  %s#%d' % (inp.transaction_id, inp.index))

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.info(f'Submitted tx with id={tx_signed.id}')

        return tx_signed

    # TODO get this working for the case where the utxo is confirmed + consumed between polls
    def wait_for_confirmation(self, tx: Transaction, max_seconds: int = 300, interval_seconds: int = 5):
        LOG.debug('ElectionPublisher.wait_for_confirmation')
        tx_id = str(tx.id) # TODO is this the right way?
        LOG.info(f'Waiting up to {max_seconds} seconds for tx {tx_id} to be confirmed on chain...')
        waited_seconds = 0
        while True:
            time.sleep(interval_seconds)
            waited_seconds += interval_seconds
            utxo = OGMIOS_CTX.utxo_by_tx_id(tx_id, 0)
            if utxo is None:
                msg = f'tx {tx_id} not confirmed after {waited_seconds} seconds.'
                remaining_seconds = max_seconds - waited_seconds
                if remaining_seconds <= 0:
                    LOG.error(msg)
                    raise Exception(msg)
                else:
                    msg += f' Will wait {remaining_seconds} more.'
                    LOG.debug(msg)
            else:
                LOG.info(f'tx {tx_id} confirmed after {waited_seconds} seconds')
                return
