import time
from pathlib import Path
from typing import List, Optional
from ..core import *
from pycardano import *
from dataclasses import replace
import logging

LOG = logging.getLogger(__name__)

# TODO how should this relate to the eventual Quart server? guess it's the backend/model?

class AdminNode(ElectionNode):

    def __init__(
        self,

        election: ElectionContext,

        # Takes a key pair rather than dir + name by default, because the
        # VerificationKeyHash needs to be known by the Funder when creating the
        # admin STT. We can't create the Admin itself at that point though,
        # because there's no ElectionContext yet.
        wallet: Wallet,

        # TODO ipfs (kubo)
    ):
        LOG.debug('Admin.__init__')
        super().__init__(
            role='admin',
            role_index=1,
            election=election,
            wallet=wallet
        )

    # TODO new function like sign_and_submit for single-output continutions if this works
    # TODO how to refactor this for admin vs subchannels?
    # TODO should this go in the base class?
    def post_public_records(
            self,
            new_records: List[PublicRecord],
            new_phase: Optional[ElectionPhase] = None,
        ) -> Transaction:

        LOG.debug('Admin.post_public_records')

        admin_collateral = wait_for_collateral(self.publisher.wallet.addr)
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))

        time.sleep(OGMIOS_POLL_SEC) # TODO remove?

        (in_utxo, in_datum) = self.state()

        assert isinstance(in_datum, ChannelState)
        LOG.debug('in_datum: %s' % pformat(in_datum))

        in_state: AdminChannelState = in_datum.state
        assert isinstance(in_state, AdminChannelState)
        LOG.debug('in_state: %s' % pformat(in_state))

        out_state: AdminChannelState = replace(
            in_state,
            new_records = new_records,
            phase = in_state.phase if new_phase is None else new_phase,
            seq = in_state.seq + 1,
        )
        assert isinstance(out_state, AdminChannelState)
        LOG.debug('out_state: %s' % pformat(out_state))

        out_datum = AdminChannel(state=out_state)
        assert isinstance(out_datum, ChannelState)
        LOG.debug('out_datum: %s' % pformat(out_datum))

        # We need the in_value alone because PyCardano will use it to
        # calculate the inputs, so create a separate out_value to mess with.
        in_value = in_utxo.output.amount
        out_value = Value.from_primitive(in_value.to_primitive())  # deep copy

        out_utxo = TransactionOutput(
            address=self.election.address,
            amount=out_value,
            datum=out_datum,
        )

        # LOG.debug('out_utxo before top-up: %s' % pformat(out_utxo))
        # top_up_to_min_ada(out_utxo)
        # LOG.debug('out_utxo after top-up: %s' % pformat(out_utxo))

        # Create the redeemer with ex_units=None so the builder's
        # _consolidate_redeemer puts it into "needs estimation" mode (ExecutionUnits(0,0)).
        redeemer = Redeemer(data=PostPublicRecords())

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(
                in_utxo,
                script=self.election.script.spend_script,
                redeemer=redeemer
            )
            .add_output(out_utxo)
        )
        txb.collaterals.append(admin_collateral)
        txb.required_signers = [self.publisher.wallet.vkh]

        # 1. Have Ogmios compute real ex_units, write them onto the redeemers.
        evaluate_and_set_ex_units(txb, out_utxo, [redeemer])

        # 2. Now that ex_units are pinned, converge fee + output coin.
        set_out_value_and_fee(txb, out_utxo)

        # tx  = self.publisher.sign_and_submit(txb)


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

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.debug(f'Submitted tx with id={tx_signed.id}')

        return tx_signed

    # TODO once both work, factor common parts out of this + post_public_records
    def add_subchannels(
            self,
            subchannels: dict[ChannelId, VerificationKeyHash],
            subchannel_ada: int = 10, # TODO proper default constant
            done_onboarding: bool = False,
        ) -> Transaction:

        LOG.debug('Admin.add_subchannels')

        # ensure own collateral
        admin_collateral = wait_for_collateral(self.publisher.wallet.addr)
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))
        time.sleep(OGMIOS_POLL_SEC)

        (in_utxo, in_datum) = self.state()
        LOG.debug('in_datum: %s' % pformat(in_datum))

        in_state: AdminChannelState = in_datum.state
        LOG.debug('in_state: %s' % pformat(in_state))

        # Create the redeemer with ex_units=None so the builder's
        # _consolidate_redeemer puts it into "needs estimation" mode (ExecutionUnits(0,0)).
        sub_ids = list(subchannels.keys()) # TODO sort?
        admin_spend_redeemer = Redeemer(data=AddSubChannels(channels=sub_ids))
        LOG.debug('admin_spend_redeemer: %s' % pformat(admin_spend_redeemer))

        # TODO more comprehensive guards based on subscriber phase
        assert in_state.phase == ElectionConfigPhase(phase=ConfigOnboardingPhase())
        next_phase = ElectionConfigPhase(phase=ConfigCeremonyPhase())

        admin_out_state: AdminChannelState = replace(
            in_state,
            subchannels = in_state.subchannels + sub_ids, # TODO sort? assert unique?
            new_records = [],
            phase = next_phase if done_onboarding else in_state.phase,
            seq = in_state.seq + 1,
        )
        LOG.debug('admin_out_state: %s' % pformat(admin_out_state))

        admin_out_datum = AdminChannel(state=admin_out_state)
        LOG.debug('admin_out_datum: %s' % pformat(admin_out_datum))

        # We need the in_value alone because PyCardano will use it to
        # calculate the inputs, so we do a deep copy first.
        in_value = in_utxo.output.amount
        admin_out_value = Value.from_primitive(in_value.to_primitive())  # deep copy

        # Adjust out value by by everything we expect to use except the TX fee.
        # TODO would it make more sense to adjust this during iteration below?
        # TODO or is there no need to pre-set it at all?
        to_fee_pools  = len(subchannels) * LOVELACE_PER_ADA * subchannel_ada
        to_collateral = len(subchannels) * COLLATERAL_LOVELACE
        admin_out_value -= to_fee_pools
        admin_out_value -= to_collateral
        LOG.debug(f'initial admin_out_value: {admin_out_value}')

        admin_out_utxo = TransactionOutput(
            address = self.election.address,
            amount  = admin_out_value,
            datum   = admin_out_datum,
        )

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(
                in_utxo,
                script=self.election.script.spend_script,
                redeemer=admin_spend_redeemer
            )
            .add_output(admin_out_utxo)
        )


        # Accumulate the mint across all subchannels so it ends up as a single
        # MultiAsset under one policy_id.
        mint_assets = MultiAsset()

        # Add the STT and fee pool ADA for each subchannel
        for (sub_id, sub_vkh) in subchannels.items():

            stt_assets = mint_channel_stt_assets(self.election.script.policy_id, 1, [sub_id])
            LOG.debug(f'{sub_id} stt_assets: {pformat(stt_assets)}')

            mint_assets += stt_assets

            stt_amt = Value(subchannel_ada * LOVELACE_PER_ADA, stt_assets)
            LOG.debug(f'{sub_id} stt_amt: {pformat(stt_amt)}')

            stt_datum = SubChannel(state=SubChannelState(
                channel_id  = sub_id,
                publisher   = sub_vkh.payload, # TODO is this right?
                new_records = [],
                seq         = 0,
            ))
            LOG.debug(f'{sub_id} stt_datum: {pformat(stt_datum)}')

            stt_utxo = TransactionOutput(
                address = self.election.address,
                amount  = stt_amt,
                datum   = stt_datum,
            )
            LOG.debug(f'{sub_id} stt_utxo: {pformat(stt_utxo)}')

            txb.add_output(stt_utxo)

        # Send subchannel publishers their collateral
        for (sub_id, sub_vkh) in subchannels.items():

            sub_addr = addr_for_vkh(sub_vkh)
            LOG.debug(f'{sub_id} sub_addr: {sub_addr}')

            col_utxo = TransactionOutput(
                address = sub_addr,
                amount = Value(coin=COLLATERAL_LOVELACE),
            )
            LOG.debug(f'{sub_id} col_utxo: {pformat(col_utxo)}')

            txb.add_output(col_utxo)


        # Tell the builder to actually mint the STTs.
        txb.mint = mint_assets

        mint_redeemer = Redeemer(data=AddSubChannels(channels=sub_ids))
        LOG.debug(f'mint_redeemer: {mint_redeemer}')

        txb.add_minting_script(script=self.election.script.mint_script, redeemer=mint_redeemer)

        # Add our own collateral for this contract interaction
        txb.collaterals.append(admin_collateral)
        txb.required_signers = [self.publisher.wallet.vkh]

        # 1. Have Ogmios compute real ex_units, write them onto the redeemer.
        evaluate_and_set_ex_units(txb, admin_out_utxo, [admin_spend_redeemer])
        LOG.debug(f'adjusted admin redeemer with ex_units: {admin_spend_redeemer}')

        # 2. Now that ex_units are pinned, converge fee + output coin.
        set_out_value_and_fee(txb, admin_out_utxo)
        LOG.debug(f'adjusted admin_out_value: {admin_out_value}')

        # 3. Final body (bakes script_data_hash from the now-final redeemer).
        tx_body = txb._build_tx_body()

        # Sanity check: inputs balance outputs.
        total_in = sum(u.output.amount.coin for u in txb.inputs) # TODO tx_body?
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

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.debug(f'Submitted tx with id={tx_signed.id}')

        return tx_signed
