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

from .ogmios   import *
from .election import ElectionContext
from .wallet   import *
from .plutus   import *

from pycardano import *

class ElectionPublisher:

    def __init__(
        self,

        # Election role and index: "guardian1", "verifier2" etc.
        # Funders and Admins don't need the index.
        # TODO restrict it to 1 in those cases?
        role: str,
        role_index: int,

        # No need for keys_dir or key_name if you pass an existing wallet.
        # You can also omit them without passing wallet, in which case a new
        # Wallet will generated based on the role + index and saved in the
        # default dir.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

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

        if wallet is None:
            LOG.debug('wallet is None; create new Wallet')
            if keys_dir is None:
                keys_dir = DEF_KEYS_DIR
                LOG.debug(f'keys_dir is None; default to {keys_dir}')
            keys_dir = Path(keys_dir) # TODO ok if already a Path?
            if key_name is None:
                key_name = channel_id_to_string(self.channel_id())
                LOG.debug(f'key_name is None; default to {key_name}')
            self.wallet = Wallet(keys_dir=keys_dir, name=key_name, verbose=False)
        else:
            LOG.debug(f'use existing wallet {wallet}')
            self.wallet = wallet

        # Lovelace per TX submitted. Useful to estimate what future elections
        # will cost, and to make sure that we aren't forgetting anything in the
        # test cleanup fns.
        self.fee_history: list[int] = []

    def channel_id(self) -> ChannelId:
        LOG.debug('ElectionPublisher.channel_id')
        if self.role in ['funder', 'admin']:
            # TODO is there ever a need for the Funder's "channel_id", since there's no channel?
            channel_str = self.role
        else:
            channel_str = f'{self.role}{self.role_index}'
        return coerce_channel_id(channel_str)

    def sign_and_submit_tx(self, txb: TransactionBuilder):
        LOG.debug('ElectionPublisher.sign_and_submit')

        # Check what the node actually sees
        utxos = OGMIOS_CTX.utxos(self.wallet.addr)
        LOG.debug('UTxOs at publisher address: %s' % len(utxos))
        for u in utxos:
            LOG.debug(
                '  %s#%d  (%d lovelace)' % (
                u.input.transaction_id, u.input.index, u.output.amount.coin
                if isinstance(u.output.amount, Value) else u.output.amount)
            )

        tx_signed = txb.build_and_sign(
            [self.wallet.sk],
            change_address=self.wallet.addr
        )

        return self.submit_tx(tx_signed)

    def submit_tx(self, tx_signed: Transaction):

        # Log the actual inputs in the built transaction
        LOG.debug('tx inputs:')
        for inp in tx_signed.transaction_body.inputs:
            LOG.debug('  %s#%d' % (inp.transaction_id, inp.index))

        fee = tx_signed.transaction_body.fee

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))

        try:
            OGMIOS_CTX.submit_tx(tx_signed) # always returns None?
            LOG.debug(f'Submitted tx with id={tx_signed.id}')
            self.fee_history.append(fee)
            LOG.debug(f'{self.channel_str()} fees so far: {self.total_fees()} Lovelace')
            return tx_signed
        except Exception as e:
            LOG.debug(f'Failed to submit tx with id={tx_signed.id}')
            raise

    # TODO get this working for the case where the utxo is confirmed + consumed between polls
    def wait_for_confirmation(
            self,
            tx: Transaction,
            # max_seconds: int = 300,
            # interval_seconds: int = 5
        ):
        LOG.debug('ElectionPublisher.wait_for_confirmation')
        tx_id = str(tx.id) # TODO is this the right way?
        LOG.debug(
            f'Waiting up to {OGMIOS_TIMEOUT_SEC} seconds for tx '
            f'{tx_id} to be confirmed.'
        )
        waited_seconds = 0
        while True:
            time.sleep(OGMIOS_POLL_SEC)
            waited_seconds += OGMIOS_POLL_SEC
            utxo = OGMIOS_CTX.utxo_by_tx_id(tx_id, 0)
            if utxo is None:
                msg = f'tx {tx_id} not confirmed after {waited_seconds} seconds.'
                remaining_seconds = OGMIOS_TIMEOUT_SEC - waited_seconds
                if remaining_seconds <= 0:
                    LOG.error(msg)
                    raise Exception(msg)
                else:
                    msg += f' Will wait {remaining_seconds} more.'
                    LOG.debug(msg)
            else:
                LOG.debug(f'tx {tx_id} confirmed after {waited_seconds} seconds')
                return

    def total_fees(self) -> int:
        return sum(self.fee_history)
