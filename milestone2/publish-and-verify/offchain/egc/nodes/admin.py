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

    def advance_phase(
            self,
            new_phase: ElectionPhase,
        ) -> Transaction:

        LOG.debug('AdminNode.advance_phase')

        ch_str = self.channel_str()
        tx_msgs = []

        # ensure own collateral
        admin_collateral = wait_for_collateral(self.publisher.wallet.addr)
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))

        (in_utxo, in_datum) = self.state()
        LOG.debug('in_datum: %s' % pformat(in_datum))

        in_state: AdminChannelState = in_datum.state
        LOG.debug('in_state: %s' % pformat(in_state))

        cont_redeemer = Redeemer(data=AdvancePhase())
        LOG.debug('cont_redeemer: %s' % pformat(cont_redeemer))

        cont_state: AdminChannelState = replace(
            in_state,
            new_records = [],
            phase = new_phase,
            seq = in_state.seq + 1,
        )
        LOG.debug('cont_state: %s' % pformat(cont_state))

        tx_msgs.append(f'{ch_str} advanced phase to {new_phase}')

        cont_datum = AdminChannel(state=cont_state)
        LOG.debug('cont_datum: %s' % pformat(cont_datum))

        # See ElectionNode.post_public_records for more on this pattern:
        cont_value = Value.from_primitive(in_utxo.output.amount.to_primitive())
        cont_utxo = TransactionOutput(
            address = self.election.address,
            amount  = cont_value,
            datum   = cont_datum,
        )

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(
                in_utxo,
                script=self.election.script.spend_script,
                redeemer=cont_redeemer
            )
            .add_output(cont_utxo)
        )

        # Add our own collateral for this contract interaction
        txb.collaterals.append(admin_collateral)

        # Add our own signature
        txb.required_signers = [self.publisher.wallet.vkh]

        tx_signed = self.balance_and_sign_state_transition_tx(
            txb,
            cont_utxo,
            cont_redeemer,
        )

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.debug(f'Submitted tx with id={tx_signed.id}')

        for msg in tx_msgs:
            LOG.info(msg)

        return tx_signed


    def add_subchannels(
            self,
            subchannels: dict[ChannelId, VerificationKeyHash],
            subchannel_ada: int = 10, # TODO proper default constant
            done_onboarding: bool = False,
        ) -> Transaction:

        LOG.debug('AdminNode.add_subchannels')

        ch_str = self.channel_str()
        tx_msgs = []

        # ensure own collateral
        admin_collateral = wait_for_collateral(self.publisher.wallet.addr)
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))

        (in_utxo, in_datum) = self.state()
        LOG.debug('in_datum: %s' % pformat(in_datum))

        in_state: AdminChannelState = in_datum.state
        LOG.debug('in_state: %s' % pformat(in_state))

        sub_ids = list(subchannels.keys()) # TODO sort?
        cont_redeemer = Redeemer(data=AddSubChannels(channels=sub_ids))
        LOG.debug('cont_redeemer: %s' % pformat(cont_redeemer))

        # TODO more comprehensive guards based on subscriber phase
        assert in_state.phase == ElectionConfigPhase(phase=ConfigOnboardingPhase())
        new_phase = ElectionConfigPhase(phase=ConfigCeremonyPhase())

        cont_state: AdminChannelState = replace(
            in_state,
            subchannels = in_state.subchannels + sub_ids, # TODO sort? assert unique?
            new_records = [],
            phase = new_phase if done_onboarding else in_state.phase,
            seq = in_state.seq + 1,
        )
        LOG.debug('cont_state: %s' % pformat(cont_state))

        cont_datum = AdminChannel(state=cont_state)
        LOG.debug('cont_datum: %s' % pformat(cont_datum))

        # See ElectionNode.post_public_records for more on this pattern:
        cont_value = Value.from_primitive(in_utxo.output.amount.to_primitive())
        cont_utxo = TransactionOutput(
            address = self.election.address,
            amount  = cont_value,
            datum   = cont_datum,
        )

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(
                in_utxo,
                script=self.election.script.spend_script,
                redeemer=cont_redeemer
            )
            .add_output(cont_utxo)
        )

        # Accumulate the mint across all subchannels so it ends up as a single
        # MultiAsset under one policy_id.
        mint_assets = MultiAsset()

        # Add the STT and fee pool ADA for each subchannel
        for (sub_id, sub_vkh) in subchannels.items():
            sub_str = channel_id_to_string(sub_id)

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
            tx_msgs.append(
                f'{ch_str} minted {sub_str} channel STT and locked {subchannel_ada} ADA from admin channel fee pool with it to pay fees.'
            )

        # Send subchannel publishers their collateral
        for (sub_id, sub_vkh) in subchannels.items():
            sub_str = channel_id_to_string(sub_id)

            sub_addr = addr_for_vkh(sub_vkh)
            LOG.debug(f'{sub_id} sub_addr: {sub_addr}')

            col_utxo = TransactionOutput(
                address = sub_addr,
                amount = Value(coin=COLLATERAL_LOVELACE),
            )
            LOG.debug(f'{sub_id} col_utxo: {pformat(col_utxo)}')

            txb.add_output(col_utxo)
            tx_msgs.append(f'{ch_str} sent 5 ADA from admin channel fee pool to {sub_str} for use as collateral.')

        if done_onboarding:
            tx_msgs.append(f'{ch_str} advanced phase to {new_phase}')

        # Tell the builder to actually mint the STTs.
        txb.mint = mint_assets
        mint_redeemer = Redeemer(data=AddSubChannels(channels=sub_ids))
        LOG.debug(f'mint_redeemer: {mint_redeemer}')
        txb.add_minting_script(script=self.election.script.mint_script, redeemer=mint_redeemer)

        # Add our own collateral for this contract interaction
        txb.collaterals.append(admin_collateral)

        # Add our own signature
        txb.required_signers = [self.publisher.wallet.vkh]

        tx_signed = self.balance_and_sign_state_transition_tx(
            txb,
            cont_utxo,
            cont_redeemer,
        )

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.debug(f'Submitted tx with id={tx_signed.id}')

        for msg in tx_msgs:
            LOG.info(msg)

        return tx_signed
