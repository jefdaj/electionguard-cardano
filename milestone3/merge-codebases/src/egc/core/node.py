import asyncio
import time
from dataclasses import replace
from pathlib import Path
from typing import List, Optional
from pycardano import *

from .ogmios     import *
from .publisher  import *
from .subscriber import *
from .election   import *
from .plutus     import *
from .ipfs       import *

import logging

LOG = logging.getLogger(__name__)


class ElectionNode:

    def __init__(
        self,

        # For deriving the ChannelId and naming state dirs.
        # Observers still get these to simplify tests, but they never go on chain.
        role: str,
        role_index: int,

        # May both be None in case of an observer.
        # All other roles should set them both from the beginning.
        # script: Optional[ElectionScript] = None,
        election_cfg: Optional[ElectionConfig] = None,

        # No need for keys_dir or key_name if you pass an existing wallet.
        # You can also omit them without passing wallet, in which case a new
        # Wallet will generated based on the role + index and saved in the
        # default dir. This logic is handled by the Publisher.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

        # TODO mk_ipfs or similar?
    ):
        LOG.debug('ElectionNode.__init__')

        # May be None in case of an Observer.
        # self.script: Optional[Script] = script
        self.config: Optional[ElectionConfig] = election_cfg

        # Always exists, but may not be used for anything in case of an Observer.
        self.publisher = ElectionPublisher(
            role       = role,
            role_index = role_index,
            wallet     = wallet,
            keys_dir   = keys_dir,
            key_name   = key_name,
        )

        # if self.script is None:
        #     LOG.debug('ElectionNode skipping subscriber init because script is None')
        #     self.subscriber = None

        # else:
        if self.config is None:
            LOG.debug('ElectionNode skipping subscriber init because config is None')
            self.subscriber = None
            self.election = None
        else:
            self.subscribe(self.config)
            # TODO wait for first event here?
            # time.sleep(OGMIOS_POLL_SEC + 1) # TODO how long is actually needed?

        LOG.info(f'Started {self.channel_str()} node.')

    def subscribe(self, cfg: ElectionConfig):
        self.election = ElectionContext.from_config(cfg)
        self.subscriber = ElectionSubscriber(
            election    = self.election,
            on_event    = lambda x: None,
            on_rollback = lambda x: None,
        )
        # TODO set self.script here
        self.subscriber.start()

    # def _guard_script(self):
    #     if self.script is None:
    #         raise Exception('Add a script first')

    def channel_id(self) -> Optional[ChannelId]:
        return self.publisher.channel_id()

    def channel_str(self) -> str:
        return self.publisher.channel_str()

    def current_utxo(self, channel_id=None) -> Optional[UTxO]:
        if channel_id is None:
            channel_id = self.channel_id()
        return self.subscriber.current_utxo(channel_id)

    def current_state(self, channel_id=None) -> Optional[UTxO]:
        if channel_id is None:
            channel_id = self.channel_id()
        return self.subscriber.current_state(channel_id)

    def current_phase(self) -> EgcPhase:
        if self.subscriber is None:
            return EgcPhase.NOT_INDEXED
        return self.subscriber.current_phase()

    def wait_for_confirmation(self, tx: Transaction):
        # TODO how to handle cases not indexed by STT cleanly? (collateral etc)

        ch_str = self.channel_str()
        tx_str = str(tx.id)

        self.publisher.wait_for_confirmation(tx)
        LOG.debug(f'{ch_str} publisher confirmed tx {tx.id}')

        self.subscriber.wait_for_confirmation(tx_str)
        LOG.debug(f'{ch_str} subscriber confirmed tx {tx.id}')

    def wait_for_phase(self, phase: Optional[ElectionPhase], timeout=OGMIOS_TIMEOUT_SEC):
        self.subscriber.wait_for_phase(phase, timeout=timeout)

    def balance_and_sign_state_transition_tx(
            self,
            txb: TransactionBuilder,
            cont_utxo: UTxO,
        ) -> Transaction:

        """Balance a transaction where rather than using a change address as
        PyCardano assumes, we want the deduct it from the value of cont_utxo
        (the STT continuation). This requires some specific setup of the
        builder and cont_utxo. See post_public_records below
        for an example."""

        # 1. Have Ogmios compute real ex_units, write them onto the redeemers.
        ogmios_retry(
            lambda: evaluate_and_set_ex_units(txb, cont_utxo)
        )

        # 2. Now that ex_units are pinned, converge fee + output coin.
        set_out_value_and_fee(txb, cont_utxo)

        # 3. Final body (bakes script_data_hash from the now-final redeemer).
        tx_body = txb._build_tx_body()

        # Sanity check: inputs balance outputs.
        total_in = sum(u.output.amount.coin for u in txb.inputs)
        total_out = sum(o.amount.coin for o in tx_body.outputs)
        assert total_in == total_out + tx_body.fee, (
            f"Unbalanced: in={total_in}, out={total_out}, fee={tx_body.fee}"
        )

        # Witness set + sign body hash.
        witness_set = txb.build_witness_set()
        if witness_set.vkey_witnesses is None:
            witness_set.vkey_witnesses = []

        signature = self.publisher.wallet.sk.sign(tx_body.hash())
        witness_set.vkey_witnesses.append(
            VerificationKeyWitness(self.publisher.wallet.vk, signature)
        )

        tx_signed = Transaction(
            transaction_body        = tx_body,
            transaction_witness_set = witness_set,
            auxiliary_data          = txb.auxiliary_data,
        )

        return tx_signed

    def post_public_records(
            self,
            new_record_pairs: List[tuple[dict, PublicRecordMetadata]],
            new_phase: Optional[ElectionPhase] = None,
        ) -> Transaction:

        LOG.debug('ElectionNode.post_public_records')

        assert len(new_record_pairs) > 0, 'post_public_records new_record_pairs empty'

        ch_str = self.channel_str()

        new_objs  = [p[0] for p in new_record_pairs]
        new_metas = [p[1] for p in new_record_pairs]
        LOG.debug('new_objs: %s' % pformat(new_objs))
        LOG.debug('new_metas: %s' % pformat(new_metas))

        new_cids: list[bytes] = ipfs_publish_objs_sync(new_objs)
        LOG.debug('new_cids: %s' % pformat(new_cids))

        assert len(new_cids) == len(new_metas)

        new_records = [
            PublicRecord(ipfs_cid=c, metadata=m)
            for (c, m) in zip(new_cids, new_metas)
        ]
        LOG.debug('new_records: %s' % pformat(new_records))

        tx_msgs = []

        pub_col_utxo = self.publisher.wait_for_collateral()
        LOG.debug('pub_col_utxo: %s' % pformat(pub_col_utxo))

        # (in_utxo, in_datum) = self.state()
        in_utxo  = self.current_utxo()
        in_datum = self.current_state()

        # in_datum should be one of the ChannelState wrapper types:
        # AdminChannel or SubChannel. Whichever type it is will be re-used
        # throughout.
        assert isinstance(in_datum, ChannelState)
        LOG.debug('in_datum: %s' % pformat(in_datum))

        # Same goes with the inner state type: re-use to match original type.
        in_state = in_datum.state
        # assert isinstance(in_state, AdminChannelState)
        LOG.debug('in_state: %s' % pformat(in_state))

        out_state = replace(
            in_state,
            new_records = new_records,
            seq = in_state.seq + 1,
        )

        if isinstance(out_state, AdminChannelState):
            out_state = replace(
                out_state,
                phase = in_state.phase if new_phase is None else new_phase,
            )
        else:
            assert new_phase is None, f'{ch_str} tried to advance phase, but is not an admin'

        # assert isinstance(out_state, AdminChannelState)
        LOG.debug('out_state: %s' % pformat(out_state))

        for record in new_records:
            tx_msgs.append(f'{ch_str} posted {record}')

        # Re-wrap in original ChannelState type.
        out_datum = replace(in_datum, state=out_state)
        assert isinstance(out_datum, ChannelState)
        LOG.debug('out_datum: %s' % pformat(out_datum))

        # The continuation UTXO will have its ADA value auto-adjusted to make the
        # TX balance, but needs the other assets to be correct already. So we
        # start with a copy of the in_utxo Value with the STT. The original
        # is left alone (not mutated) so we don't mess up PyCardano calculations.
        cont_value = Value.from_primitive(in_utxo.output.amount.to_primitive()) # deep copy
        cont_addr = Address(self.election.script.policy_id, network=Network.TESTNET) # TODO dynamic network
        cont_utxo = TransactionOutput(
            address = cont_addr,
            amount  = cont_value,
            datum   = out_datum,
        )

        # The continuation redeemer will have its ex_units set to make the TX
        # balance, so it's important not to set them here.
        cont_redeemer = Redeemer(data=PostPublicRecords())

        # TX building is pretty standard other than the cont_* parts above.
        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(
                in_utxo,
                script=self.election.script.spend_script,
                redeemer=cont_redeemer
            )
            .add_output(cont_utxo)
        )
        txb.collaterals.append(pub_col_utxo)
        txb.required_signers = [self.publisher.wallet.vkh]

        # Fancy stuff here.
        tx_signed = self.balance_and_sign_state_transition_tx(
            txb,
            cont_utxo,
        )

        self.publisher.submit_tx(tx_signed)

        if new_phase is not None:
            tx_msgs.append(f'{ch_str} advanced phase to {new_phase}')

        for msg in tx_msgs:
            LOG.info(msg)

        return tx_signed

    def return_collateral(self):
        # TODO special case for the admin to return ALL collateral to funder here?
        # TODO or everyone return it to funder individually?
        # TODO only auto return if collateral originally came from admin/funder
        # if getattr(self, 'election', None) is None:
        #     raise Exception('No election, so no funder_address.')
        # TODO return collateral to the channel rather than a person?
        # return_addr = self.subscriber.admin_address()
        return_addr = self.election.deployment.funder_address
        return self.publisher.return_collateral(return_addr)

    def stop(self):
        if self.subscriber is not None:
            self.subscriber.stop()
            self.subscriber.join()
        LOG.info(f'Stopped {self.channel_str()} node.')

    def _build_burn_tx(self) -> Tuple[List[str], TransactionBuilder]:

        # Without this set, the FunderNode risks the entire dev wallet when
        # deploying a contract.
        self.publisher.create_own_collateral()
        funder_collateral = self.publisher.wait_for_collateral()

        # Messages to log if/when the TX succeeds
        ch_str = self.channel_str()
        tx_msgs = []

        mint_redeemer = Redeemer(data=BurnTestTokens())
        LOG.debug(f'mint_redeemer: {mint_redeemer}')

        # TODO why is this failing? seems to not get the message that STTs have been burned?
        channel_ids = self.subscriber.current_channel_ids()
        LOG.debug(f'channel_ids: {channel_ids}')

        if len(channel_ids) == 0:
            # shouldn't normally happen
            LOG.debug(f'subscriber history:\n{pformat(self.subscriber._history)}')
            msg = 'skip burn tx because no channels to burn'
            LOG.error(msg)
            raise RuntimeError(msg)

        burn_assets = mint_channel_stt_assets(
            self.election.script.policy_id,
            -1,
            channel_ids,
        )
        LOG.debug(f'burn_assets: {burn_assets}')

        burn_txb = (
            TransactionBuilder(OGMIOS_CTX, mint=burn_assets)
            .add_minting_script(script=self.election.script.mint_script, redeemer=mint_redeemer)
        )

        burn_txb.collaterals.append(funder_collateral)

        for channel_id in channel_ids:
            ch_str = channel_id_to_string(channel_id)
            utxo = self.subscriber.current_utxo(channel_id)
            LOG.debug(f'{ch_str} STT UTXO to spend: {utxo}')
            spend_redeemer = Redeemer(data=BurnTestTokens())
            burn_txb = burn_txb.add_script_input(
                utxo,
                script=self.election.script.spend_script,
                redeemer=spend_redeemer
            )
            tx_msgs.append(f'{ch_str} burned {ch_str} channel STT and recovered fee pool ADA.')

        LOG.debug('burn_txb:\n%s\n' % pformat(burn_txb))

        return (tx_msgs, burn_txb)

    def burn_test_tokens(self):
        """Clean up test tokens.

        WARNING: The on-chain code lets anyone do this, not just the funder.
        BurnTestTokens should be removed before production use.
        """
        if not 'burntesttokens' in EGC_PLUTUS_MODE:
            err = f"burn_test_tokens does not work in EGC_PLUTUS_MODE={EGC_PLUTUS_MODE}"
            LOG.error(err)
            raise RuntimeError(err)
        # if self.election is None:
        #     raise Exception('init_election must be called before burn_test_tokens')
        if self.subscriber is None:
            raise Exception('init_subscriber must be called before burn_test_tokens')
        (tx_msgs, burn_txb) = self._build_burn_tx()
        burn_tx  = self.publisher.sign_and_submit_tx(burn_txb)
        # json_path = self.election_json_path()
        for msg in tx_msgs:
            LOG.info(msg)
        ch_str = self.channel_str()
        # LOG.info(f'{ch_str} burned all test tokens and recovered fee pool ADA from {json_path}')
        return burn_tx

    def recover_all_collateral(self, keys_dir: Path) -> Transaction:
        if EGC_WALLET_MODE != 'scripted':
            err = f"recover_all_collateral requires EGC_WALLET_MODE=scripted, not '{EGC_WALLET_MODE}'"
            LOG.error(err)
            raise RuntimeError(err)
        ch_str = self.channel_str()
        errors = []
        last_tx = None # only have to wait once

        for channel_id in self.subscriber.all_channel_ids():

            # Can't use the current state because the channel may be closed.
            # But it should have either an input or output at least.
            with self.subscriber._history_lock:
                event = self.subscriber._history[channel_id][-1]
                if event.output_state:
                    state = event.output_state
                else:
                    state = event.input_state

            try:
                LOG.debug(f'state: {state}')
                pub_addr   = publisher_address(state)
                LOG.debug(f'pub_addr: {pub_addr}')
                (sk_path, pub_wallet) = load_wallet_by_address(pub_addr, keys_dir=keys_dir)
                LOG.debug(f'sk_path: {sk_path}')
                LOG.debug(f'pub_wallet: {pub_wallet}')
                tx = self.publisher.return_collateral(
                    self.publisher.wallet.addr,
                    from_wallet = pub_wallet,
                )
                if tx is not None:
                    last_tx = tx
                    LOG.info(f'{ch_str} recovered collateral from {sk_path}')
                else:
                    LOG.info(f'{ch_str} has no collateral UTXO. Already returned?')
            except Exception as e:
                LOG.exception(f'{ch_str} failed to recover collateral from {pub_addr}')
                errors.append(e)
        if errors:
            raise ExceptionGroup('recover_all_collateral had failures', errors)
        return last_tx
