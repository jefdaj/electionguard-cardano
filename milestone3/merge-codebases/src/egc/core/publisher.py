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

        # TODO add explicit wallet creation to tests + docs
        # if wallet is None:
        #     LOG.debug('wallet is None; create new Wallet')
        #     if keys_dir is None:
        #         keys_dir = DEF_KEYS_DIR
        #         LOG.debug(f'keys_dir is None; default to {keys_dir}')
        #     keys_dir = Path(keys_dir) # TODO ok if already a Path?
        #     if key_name is None:
        #         key_name = channel_id_to_string(self.channel_id())
        #         LOG.debug(f'key_name is None; default to {key_name}')
        #     self.wallet = Wallet(keys_dir=keys_dir, name=key_name, verbose=False)
        # else:
        #     LOG.debug(f'use existing wallet {wallet}')
        self.wallet = wallet

        # Lovelace per TX submitted. Useful to estimate what future elections
        # will cost, and to make sure that we aren't forgetting anything in the
        # test cleanup fns.
        self.fee_history: list[int] = []

    # TODO clarify: channel_id won't exist for observers, but channel_str will?
    def channel_id(self) -> Optional[ChannelId]:
        LOG.debug('ElectionPublisher.channel_id')
        if self.role in ['observer', 'funder']:
            return None
        if self.role == 'admin':
            channel_str = self.role
        else:
            channel_str = f'{self.role}{self.role_index}'
        return coerce_channel_id(channel_str)

    def channel_str(self):
        "Like channel_id, but informal for logs. Includes observer as valid."
        if self.role in ['observer', 'funder']:
            return f'{self.role}{self.role_index}'
        else:
            return channel_id_to_string(self.channel_id())
        # except:
        #    return 'funder' # TODO safer way?

    def _guard_wallet(self):
        if self.wallet is None:
            raise Exception('create a wallet first')

    def sign_and_submit_tx(self, txb: TransactionBuilder, change_addr: Optional[Address] = None):
        LOG.debug('ElectionPublisher.sign_and_submit')

        self._guard_wallet()

        # Check what the node actually sees
        utxos = ogmios_retry( lambda: OGMIOS_CTX.utxos(self.wallet.addr) )
        LOG.debug('UTxOs at publisher address: %s' % len(utxos))
        for u in utxos:
            LOG.debug(
                '  %s#%d  (%d lovelace)' % (
                u.input.transaction_id, u.input.index, u.output.amount.coin
                if isinstance(u.output.amount, Value) else u.output.amount)
            )

        if change_addr is None:
            change_addr = self.wallet.addr

        tx_signed = txb.build_and_sign(
            [self.wallet.sk],
            change_address=change_addr
        )

        return self.submit_tx(tx_signed)

    def submit_tx(self, tx_signed: Transaction):

        # Log the actual inputs in the built transaction
        # TODO remove?
        LOG.debug('tx inputs:')
        for inp in tx_signed.transaction_body.inputs:
            LOG.debug('  %s#%d' % (inp.transaction_id, inp.index))

        def submit_fn():
            fee = tx_signed.transaction_body.fee
            LOG.debug(f'tx_signed about to be submitted:\n%s\n' % pformat(tx_signed))
            OGMIOS_CTX.submit_tx(tx_signed) # always returns None?
            LOG.debug(f'Successfully submitted tx with id={tx_signed.id}')
            self.fee_history.append(fee)
            ch_str = self.channel_str()
            fee_ada = self.total_fees_ada()
            LOG.debug(f'{ch_str} fees so far: {fee_ada} ADA')
            return tx_signed

        return ogmios_retry(
            submit_fn,
        )


    # TODO get this working for the case where the utxo is confirmed + consumed between polls
    def await_tx_confirmed(
            self,
            tx: Transaction,
            output_indices=(0,), # TODO remove if we always use 0?
        ):
        LOG.debug('ElectionPublisher.await_tx_confirmed')
        if tx is None:
            LOG.debug('tx is None; not waiting for confirmation.')
            return
        tx_id = str(tx.id)
        LOG.debug(
            f'Waiting up to {OGMIOS_TIMEOUT_SEC}s for tx '
            f'{tx_id} to be confirmed.'
        )
        deadline = time.monotonic() + OGMIOS_TIMEOUT_SEC
        while True:
            if all(
                ogmios_retry( lambda: OGMIOS_CTX.utxo_by_tx_id(tx_id, i) ) is not None
                for i in output_indices
            ):
                LOG.debug(f'tx {tx_id} confirmed.') # TODO log how many seconds it took?
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(f'tx {tx_id} not confirmed in {OGMIOS_TIMEOUT_SEC}s')
            time.sleep(OGMIOS_POLL_SEC)

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
        self._guard_wallet()
        txb = TransactionBuilder(OGMIOS_CTX)
        txb.add_input_address(self.wallet.addr)
        txb.add_output(TransactionOutput(recipient, Value(lovelace)))
        # signed = txb.build_and_sign([self.wallet.sk], change_address=self.wallet.addr)
        # self.submit_tx(signed)
        tx = self.sign_and_submit_tx(txb)
        LOG.debug(
            "Sent %d lovelace from %s to %s (tx %s)",
            lovelace, self.wallet.addr, recipient, tx.id,
        )
        return tx

    def find_collateral_utxo(
            self,
            from_wallet: Optional[Wallet] = None,
            timeout = OGMIOS_TIMEOUT_SEC,
        ) -> UTxO | None:
        """Return a collateral-eligible UTXO, or None.

        "Collateral-eligible" means: exactly COLLATERAL_LOVELACE lovelace,
        no native assets, no datum, no script ref. This is stricter than
        the ledger requires, but it guarantees the UTXO matches what our
        funding functions produce and won't collide with other holdings.
        """
        if from_wallet is None:
            self._guard_wallet()
            wallet = self.wallet
        else:
            wallet = from_wallet
        utxos = ogmios_retry(
            lambda: OGMIOS_CTX.utxos(wallet.addr),
            timeout = timeout
        )
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
        self._guard_wallet()
        utxo = self.find_collateral_utxo()
        if utxo is None:
            raise RuntimeError(
                f"No collateral UTXO ({COLLATERAL_ADA} ADA, no assets, no datum) "
                f"found at {self.wallet.addr}. Run create_own_collateral or ask the "
                f"funder to send one."
            )
        return utxo

    def await_collateral(self, timeout=OGMIOS_TIMEOUT_SEC) -> UTxO:
        """Poll for a collateral UTXO at `address` until one appears or
        `timeout` seconds go by. Used right after a funding tx to bridge
        the gap between submission and the publisher's address being
        re-indexed."""
        self._guard_wallet()
        deadline = time.monotonic() + timeout
        while True:
            utxo = self.find_collateral_utxo()
            if utxo is not None:

                # TODO is this masking a bug? Not sure why it's required.
                time.sleep(OGMIOS_POLL_SEC)

                return utxo
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Collateral UTXO did not appear at {self.wallet.addr} within "
                    f"{timeout}s"
                )
            time.sleep(OGMIOS_POLL_SEC)


    def consolidate_utxos(self, max_inputs_per_tx=120) -> Transaction:
        """Mainly used to set up before testing create_own_collateral.

        This may take multiple transactions. Unlike most functions, this will
        wait to confirm all of them internally rather than returning a tx.

        Txs with native assets are larger per input than pure-ADA ones.
        Lower max_inputs_per_tx if you hit tx-too-large errors.
        """
        # TODO timeouts?

        def summarize(utxos):
            total_lovelace = 0
            asset_count = 0
            policies = set()
            for u in utxos:
                total_lovelace += u.output.amount.coin
                ma = u.output.amount.multi_asset
                if ma:
                    for pid, assets in ma.data.items():
                        policies.add(pid)
                        asset_count += len(assets)
            return total_lovelace, asset_count, len(policies)

        def consolidate_batch(utxos):
            # With no explicit outputs and a change_address, the builder sweeps
            # everything (ADA + native assets) into a single output at `addr`,
            # automatically computing the fee and respecting min-ADA for the bundle.
            txb = TransactionBuilder(OGMIOS_CTX)
            for u in utxos:
                txb.add_input(u)
            tx = self.sign_and_submit_tx(txb)
            self.await_tx_confirmed(tx)
            return

        while True:
            utxos = ogmios_retry( lambda: OGMIOS_CTX.utxos(self.wallet.addr) ) # TODO str?
            LOG.debug(f"Found {len(utxos)} UTXOs at {self.wallet.addr}")
            if len(utxos) < 2:
                LOG.info("Done consolidating UTXOs.")
                return
            total_lovelace, asset_count, policy_count = summarize(utxos)
            LOG.debug(f"Total: {total_lovelace / 1_000_000:.6f} tADA")
            LOG.debug(f"Native assets: {asset_count} across {policy_count} policies")
            batch = utxos[0:max_inputs_per_tx]
            consolidate_batch(batch)



    # TODO verify this isn't being run more often than needed
    # TODO move to FunderNode? they're the only ones generally expected to use it
    def create_own_collateral(self):
        """Funder sends themselves exactly COLLATERAL_ADA to create a
        usable collateral UTXO. No-op (returns None-ish? see below) if one
        already exists — callers that want to force a new one should spend
        the existing one first."""
        # TODO return Optional[Transcation]? txid?
        self._guard_wallet()
        ch_str = self.channel_str()
        existing = self.find_collateral_utxo()
        if existing is not None:
            LOG.debug(
                "%s found existing collateral UTXO at %s (%s#%d)",
                ch_str, self.wallet.addr,
                existing.input.transaction_id, existing.input.index,
            )
            # return existing.input.transaction_id
            return
        tx = self.send_lovelace(self.wallet.addr, COLLATERAL_LOVELACE)
        LOG.info(f'{ch_str} created own collateral UTXO at {self.wallet.addr}')
        # return tx
        return

    def return_collateral(
        self,
        return_addr: Address,
        from_wallet: Optional[Wallet] = None, # used by funder for BurnTestTokens
    ) -> Optional[TransactionId]:
        """Publisher voluntarily returns their collateral UTXO to the
        original funder, less tx fee. The publisher is expected to do this,
        but it can't be enforced on chain. Returns None if the publisher has
        no collateral UTXO to return."""
        # You probably want the version in egc/core/node.py that auto-picks return_addr.
        if from_wallet is None:
            self._guard_wallet()
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
        # signed = txb.build_and_sign(
            # [wallet.sk], change_address=return_addr,
        # )
        # tx = self.submit_tx(signed)
        tx = self.sign_and_submit_tx(txb, change_address=return_addr)
        LOG.debug(
            "%s returned collateral from %s to %s, less tx fee (tx %s)",
            self.channel_str(), wallet.addr, return_addr, tx.id,
        )
        return tx
