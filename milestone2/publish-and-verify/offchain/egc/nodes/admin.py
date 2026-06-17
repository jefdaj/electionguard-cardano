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
        admin_collateral = self.publisher.wait_for_collateral()
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))

        # (in_utxo, in_datum) = self.state()
        in_utxo  = self.current_utxo()
        in_datum = self.current_state()
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
        )

        self.publisher.submit_tx(tx_signed)

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
        admin_collateral = self.publisher.wait_for_collateral()
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))

        # (in_utxo, in_datum) = self.state()
        in_utxo  = self.current_utxo()
        in_datum = self.current_state()
        LOG.debug('admin in_utxo: %s' % pformat(in_utxo))
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
            LOG.debug(f'{sub_str} stt_assets: {pformat(stt_assets)}')

            mint_assets += stt_assets

            stt_amt = Value(subchannel_ada * LOVELACE_PER_ADA, stt_assets)
            LOG.debug(f'{sub_str} stt_amt: {pformat(stt_amt)}')

            stt_datum = SubChannel(state=SubChannelState(
                channel_id  = sub_id,
                publisher   = sub_vkh.payload, # TODO is this right?
                new_records = [],
                seq         = 0,
            ))
            LOG.debug(f'{sub_str} stt_datum: {pformat(stt_datum)}')

            stt_utxo = TransactionOutput(
                address = self.election.address,
                amount  = stt_amt,
                datum   = stt_datum,
            )
            LOG.debug(f'{sub_str} stt_utxo: {pformat(stt_utxo)}')

            txb.add_output(stt_utxo)
            tx_msgs.append(
                f'{ch_str} minted {sub_str} channel STT and locked '
                f'{subchannel_ada} ADA from admin channel with it to pay fees.'
            )

        # Send subchannel publishers their collateral
        for (sub_id, sub_vkh) in subchannels.items():
            sub_str = channel_id_to_string(sub_id)

            sub_addr = addr_for_vkh(sub_vkh)
            LOG.debug(f'{sub_str} sub_addr: {sub_addr}')

            col_utxo = TransactionOutput(
                address = sub_addr,
                amount = Value(coin=COLLATERAL_LOVELACE),
            )
            LOG.debug(f'{sub_str} col_utxo: {pformat(col_utxo)}')

            txb.add_output(col_utxo)
            tx_msgs.append(
                f'{ch_str} sent 5 ADA from admin channel fee pool to '
                f'{sub_str} for use as collateral.'
            )

        if done_onboarding:
            tx_msgs.append(f'{ch_str} advanced phase to {new_phase}')

        # Tell the builder to actually mint the STTs.
        txb.mint = mint_assets
        # TODO does this also get added to balance_and_sign...?
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
        )

        self.publisher.submit_tx(tx_signed)

        for msg in tx_msgs:
            LOG.info(msg)

        return tx_signed

    def rm_subchannels(
            self,
            subchannels: list[ChannelId],
        ) -> Transaction:

        LOG.debug('AdminNode.rm_subchannels')

        # Things to accumulate and handle together at the end of the building process.
        tx_msgs = []
        burn_assets = MultiAsset()

        # ensure own collateral
        # TODO factor out
        admin_collateral = self.publisher.wait_for_collateral()
        LOG.debug('admin_collateral: %s' % pformat(admin_collateral))

        # TODO start state transition edit section
        # (in_utxo, in_datum) = self.state()
        in_utxo  = self.current_utxo()
        in_datum = self.current_state()
        LOG.debug('in_utxo: %s' % pformat(in_utxo))
        LOG.debug('in_datum: %s' % pformat(in_datum))

        in_state: AdminChannelState = in_datum.state
        LOG.debug('in_state: %s' % pformat(in_state))

        cont_redeemer = Redeemer(data=RmSubChannels(channels=subchannels))
        LOG.debug('cont_redeemer: %s' % pformat(cont_redeemer))

        remaining_ids = [i for i in in_state.subchannels if not i in subchannels]
        LOG.debug('remaining_ids: %s' % remaining_ids)

        cont_state: AdminChannelState = replace(
            in_state,
            subchannels = remaining_ids,
            new_records = [],
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
        # TODO end state transition edit section?

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(
                in_utxo,
                script=self.election.script.spend_script,
                redeemer=cont_redeemer
            )
            .add_output(cont_utxo)
        )

        # Burn each subchannel STT, add its UTXO as an input, and add its spend redeemer
        for sub_id in subchannels:
            sub_str = channel_id_to_string(sub_id)
            sub_st = self.subscriber.current_state(sub_id)
            sub_state = sub_st.state
            # sub_utxo  = kupo_match_to_pycardano_utxo(sub_st.utxo_dict)
            sub_utxo = self.subscriber.current_utxo(sub_id)
            LOG.debug(f'{sub_str} sub_utxo: {pformat(sub_utxo)}')
            sub_assets = mint_channel_stt_assets(self.election.script.policy_id, -1, [sub_id])
            LOG.debug(f'{sub_str} sub_assets: {pformat(sub_assets)}')
            burn_assets += sub_assets

            # TODO does anything in the contract force this to be the same across all utxos?
            # TODO if not, would it make more sense to have singletons for the subchannels?
            sub_redeemer = Redeemer(data=RmSubChannels(channels=subchannels))
            LOG.debug(f'{sub_str} sub_redeemer: {sub_redeemer}')

            txb.add_script_input(
                sub_utxo,
                script=self.election.script.spend_script, # deep copy here doesn't help
                redeemer=sub_redeemer,
            )
            tx_msgs.append(
                f'admin burned {sub_str} channel STT '
                'and returned its ADA to the admin channel fee pool.'
            )

        # Tell the builder to actually burn the STTs.
        txb.mint = burn_assets
        burn_redeemer = Redeemer(data=RmSubChannels(channels=subchannels))
        LOG.debug(f'burn_redeemer: {burn_redeemer}')
        txb.add_minting_script(script=self.election.script.mint_script, redeemer=burn_redeemer)

        # Add our own collateral for this contract interaction
        # TODO factor out, either to balance_and_sign or a new fn
        txb.collaterals.append(admin_collateral)

        # Add our own signature
        # TODO move to balance_and_sign_state_transition_tx
        txb.required_signers = [self.publisher.wallet.vkh]

        tx_signed = self.balance_and_sign_state_transition_tx(
            txb,
            cont_utxo,
        )

        for tx_in in tx_signed.transaction_body.inputs:
            utxo = utxo_for_input(tx_in)
            LOG.debug(f'Input UTXO found: {utxo}')
            assert utxo is not None, f"Input UTXO not found: {tx_in}"

        self.publisher.submit_tx(tx_signed)

        for msg in tx_msgs:
            LOG.info(msg)

        return tx_signed
