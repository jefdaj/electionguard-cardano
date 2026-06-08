import time
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

        collateral_utxo = wait_for_collateral(self.publisher.wallet.addr)
        LOG.debug('collateral_utxo: %s' % pformat(collateral_utxo))

        time.sleep(OGMIOS_POLL_SEC) # TODO remove?

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
        txb.collaterals.append(collateral_utxo)
        txb.required_signers = [self.publisher.wallet.vkh]

        # 1. Have Ogmios compute real ex_units, write them onto the redeemer.
        evaluate_and_set_ex_units(txb, out_utxo, in_value, redeemer)

        # 2. Now that ex_units are pinned, converge fee + output coin.
        set_out_value_and_fee(txb, in_value, out_utxo)

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
        LOG.info(f'Submitted tx with id={tx_signed.id}')

        return tx_signed
