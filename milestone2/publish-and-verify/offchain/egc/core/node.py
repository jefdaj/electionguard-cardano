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

import logging

LOG = logging.getLogger(__name__)


class ElectionNode:

    def __init__(
        self,

        # For deriving the ChannelId
        role: str,
        role_index: int,

        # This should only be None in the case of the initial Funder,
        # since at that point there isn't an ElectionContext yet.
        election: Optional[ElectionContext] = None,

        # No need for keys_dir or key_name if you pass an existing wallet.
        # You can also omit them without passing wallet, in which case a new
        # Wallet will generated based on the role + index and saved in the
        # default dir. This logic is handled by the Publisher.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

        # TODO ipfs (kubo)
    ):
        LOG.debug('ElectionNode.__init__')

        # May be None in case of a Funder.
        self.election: Optional[ElectionContext] = election

        self.publisher = ElectionPublisher(
            role       = role,
            role_index = role_index,
            wallet     = wallet,
            keys_dir   = keys_dir,
            key_name   = key_name,
        )

        if self.election is None:
            LOG.debug('ElectionNode skipping subscriber init because election is None')
            self.subscriber = None
        else:
            sub_cfg = SubscriberConfig.from_election(self.election)
            self.subscriber = ElectionSubscriber(
                config      = sub_cfg,
                on_action   = lambda x: None,
                on_rollback = lambda x: None,
            )
            self.subscriber.start()
            time.sleep(OGMIOS_POLL_SEC + 1) # TODO how long is actually needed?

        LOG.info(f'Started {self.channel_str()} node.')

    def channel_id(self) -> ChannelId:
        return self.publisher.channel_id()

    def channel_str(self) -> str:
        return self.publisher.channel_str()

    def current_utxo(self) -> Optional[UTxO]:
        return self.subscriber.current_utxo(self.channel_id())

    def current_state(self) -> Optional[UTxO]:
        return self.subscriber.current_state(self.channel_id())

    def current_phase(self) -> Optional[ElectionPhase]:
        return self.subscriber.current_phase()

    def wait_for_confirmation(self, tx: Transaction):
        self.publisher.wait_for_confirmation(tx)
        ch_str = self.channel_str()
        LOG.debug(f'{ch_str} confirmed tx {tx.id}')
        time.sleep(OGMIOS_DELAY_SEC)

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
        evaluate_and_set_ex_units(txb, cont_utxo)

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
            new_records: List[PublicRecord],
            new_phase: Optional[ElectionPhase] = None,
        ) -> Transaction:

        LOG.debug('ElectionNode.post_public_records')

        assert len(new_records) > 0, 'post_public_records new_records empty'

        ch_str = self.channel_str()
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
        cont_utxo = TransactionOutput(
            address = self.election.address,
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

    def stop(self):
        if self.subscriber is not None:
            self.subscriber.stop()
            self.subscriber.join()
        LOG.info(f'Stopped {self.channel_str()} node.')
