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

    def channel_str(self):
        "Like channel_id, but informal for logs. Includes funder as valid."
        try:
            return channel_id_to_string(self.channel_id())
        except:
            return 'funder' # TODO safer way?

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

        LOG.debug(f'tx_signed about to be submitted:\n%s\n' % pformat(tx_signed))

        try:
            OGMIOS_CTX.submit_tx(tx_signed) # always returns None?
            LOG.debug(f'Submitted tx with id={tx_signed.id}')
            self.fee_history.append(fee)
            ch_str = self.channel_str()
            fee_ada = self.total_fees_ada()
            LOG.debug(f'{ch_str} fees so far: {fee_ada} ADA')
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
                msg = f'tx {tx_id} not confirmed after {round(waited_seconds)} seconds.'
                remaining_seconds = OGMIOS_TIMEOUT_SEC - waited_seconds
                if remaining_seconds <= 0:
                    LOG.error(msg)
                    raise Exception(msg) # TODO custom error?
                else:
                    msg += f' Will wait {round(remaining_seconds)} more.'
                    LOG.debug(msg)
            else:
                LOG.debug(f'tx {tx_id} confirmed after {round(waited_seconds)} seconds')
                return

    def total_fees_ada(self) -> float:
        return round(
            sum(self.fee_history) / LOVELACE_PER_ADA,
            ndigits=2
        )

    def send_lovelace(
        self,
        recipient: Address,
        lovelace: int,
    ) -> Transaction:
        """Plain wallet-to-wallet ADA send. Internal helper shared by the
        collateral funding / return / sweep functions. Not for spending from
        a script address."""
        txb = TransactionBuilder(OGMIOS_CTX)
        txb.add_input_address(self.wallet.addr)
        txb.add_output(TransactionOutput(recipient, Value(lovelace)))
        signed = txb.build_and_sign([self.wallet.sk], change_address=self.wallet.addr)
        self.submit_tx(signed)
        LOG.debug(
            "Sent %d lovelace from %s to %s (tx %s)",
            lovelace, self.wallet.addr, recipient, signed.id,
        )
        return signed

    def find_collateral_utxo(self, from_wallet: Optional[Wallet] = None) -> UTxO | None:
        """Return a collateral-eligible UTXO, or None.

        "Collateral-eligible" means: exactly COLLATERAL_LOVELACE lovelace,
        no native assets, no datum, no script ref. This is stricter than
        the ledger requires, but it guarantees the UTXO matches what our
        funding functions produce and won't collide with other holdings.
        """
        if from_wallet is None:
            wallet = self.wallet
        else:
            wallet = from_wallet
        utxos = OGMIOS_CTX.utxos(wallet.addr)
        for utxo in utxos:
            amt = utxo.output.amount
            if amt.coin != COLLATERAL_LOVELACE:
                continue
            if amt.multi_asset and len(amt.multi_asset) > 0:
                continue
            if utxo.output.datum is not None:
                continue
            if utxo.output.datum_hash is not None:
                continue
            if utxo.output.script is not None:
                continue
            return utxo
        return None

    # TODO use or remove
    def get_my_collateral(self) -> UTxO:
        """Like find_collateral_utxo but raises if missing. Publishers call
        this when building any contract tx and pass the result as the
        collateral input."""
        utxo = self.find_collateral_utxo()
        if utxo is None:
            raise RuntimeError(
                f"No collateral UTXO ({COLLATERAL_ADA} ADA, no assets, no datum) "
                f"found at {self.wallet.addr}. Run create_own_collateral or ask the "
                f"funder to send one."
            )
        return utxo

    # TODO unify with wait_for_confirmation?
    def wait_for_collateral(self) -> UTxO:
        """Poll for a collateral UTXO at `address` until one appears or
        OGMIOS_TIMEOUT_SEC elapses. Used right after a funding tx to bridge
        the gap between submission and the publisher's address being
        re-indexed."""
        deadline = time.monotonic() + OGMIOS_TIMEOUT_SEC
        while True:
            utxo = self.find_collateral_utxo()
            if utxo is not None:

                # TODO is this masking a bug? Not sure why it's required.
                time.sleep(OGMIOS_POLL_SEC)

                return utxo
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Collateral UTXO did not appear at {self.wallet.addr} within "
                    f"{OGMIOS_TIMEOUT_SEC}s"
                )
            time.sleep(OGMIOS_POLL_SEC)


    # TODO verify this isn't being run more often than needed
    # TODO move to FunderNode? they're the only ones generally expected to use it
    def create_own_collateral(self) -> Transaction:
        """Funder sends themselves exactly COLLATERAL_ADA to create a
        usable collateral UTXO. No-op (returns None-ish? see below) if one
        already exists — callers that want to force a new one should spend
        the existing one first."""
        ch_str = self.channel_str()
        existing = self.find_collateral_utxo()
        if existing is not None:
            LOG.debug(
                "%s found existing collateral UTXO at %s (%s#%d)",
                ch_str, self.wallet.addr,
                existing.input.transaction_id, existing.input.index,
            )
            return existing.input.transaction_id
        res = self.send_lovelace(self.wallet.addr, COLLATERAL_LOVELACE)
        LOG.info(f'{ch_str} created own collateral UTXO at {self.wallet.addr}')
        return res

    def return_collateral(
        self,
        return_addr: Address,
        from_wallet: Optional[Wallet] = None, # used by funder for BurnTestTokens
    ) -> Optional[TransactionId]:
        """Publisher voluntarily returns their collateral UTXO to the
        original funder, less tx fee. The publisher is expected to do this,
        but it can't be enforced on chain. Returns None if the publisher has
        no collateral UTXO to return."""
        if from_wallet is None:
            wallet = self.wallet
        else:
            wallet = from_wallet
        utxo = self.find_collateral_utxo(from_wallet=wallet)
        if utxo is None:
            LOG.debug(f"No collateral UTXO at {wallet.addr} to return")
            return None
        txb = TransactionBuilder(OGMIOS_CTX)
        txb.add_input(utxo)
        # No add_output / no change_address pointing at publisher — we want
        # the entire UTXO to go to the funder, minus the fee. Using the
        # funder as the change address makes the builder route the remainder
        # (collateral - fee) to them automatically.
        signed = txb.build_and_sign(
            [wallet.sk], change_address=return_addr,
        )
        self.submit_tx(signed)
        LOG.debug(
            "%s returned collateral from %s to %s, less tx fee (tx %s)",
            self.channel_str(), wallet.addr, return_addr, signed.id,
        )
        return signed
