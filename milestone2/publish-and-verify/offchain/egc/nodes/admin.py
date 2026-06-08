from pathlib import Path
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

        (in_utxo, in_datum) = self.state()
        in_state = in_datum.state
        LOG.debug('in_state: %s' % pformat(in_state))

        out_datum = AdminChannel(state=replace(
            in_state,
            new_records = new_records,
            phase = in_state.phase if new_phase is None else new_phase,
            seq = in_state.seq + 1,
        ))
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

        # Because we're bypassing build() to do a manual thing instead,
        # we have to set ex_units manually here. It can be an over estimate though;
        # they'll be lowered to their final values by set_out_value_and_fee below.
        redeemer = Redeemer(
            data=PostPublicRecords(),
            ex_units=ExecutionUnits(mem=500_000, steps=200_000_000) # TODO what are good defaults here?
        )

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(in_utxo, script=self.election.script.spend_script, redeemer=redeemer)
            .add_output(out_utxo)
        )
        txb.required_signers = [self.publisher.wallet.vkh] # TODO remove?

        set_out_value_and_fee(txb, in_value, out_utxo)

        # tx  = self.publisher.sign_and_submit(txb)

        # Build the body without letting the builder add change or recompute fee.
        # _build_tx_body() uses txb.fee as-is (which we've already pinned).
        tx_body = txb._build_tx_body()

        # Double check the manual calculations
        total_in = sum(u.output.amount.coin for u in [in_utxo])  # plus any others
        total_out = sum(o.amount.coin for o in tx_body.outputs)
        assert total_in == total_out + tx_body.fee, (
            f"Unbalanced: in={total_in}, out={total_out}, fee={tx_body.fee}"
        )

        # Witness set: Plutus script + datum + redeemer come from the builder;
        # we append the publisher's vkey witness manually.
        witness_set = txb.build_witness_set()
        if witness_set.vkey_witnesses is None:
            witness_set.vkey_witnesses = []
        
        signature = self.publisher.wallet.sk.sign(tx_body.hash())
        witness_set.vkey_witnesses.append(
            VerificationKeyWitness(self.publisher.wallet.vk, signature)
        )

        tx_signed = Transaction(
            transaction_body=tx_body,
            transaction_witness_set=witness_set,
            auxiliary_data=txb.auxiliary_data,
        )

        LOG.debug(f'tx_signed about to be submitted:\n%s:\n' % pformat(tx_signed))
        OGMIOS_CTX.submit_tx(tx_signed)
        LOG.info(f'Submitted tx with id={tx_signed.id}')

        return tx_signed
