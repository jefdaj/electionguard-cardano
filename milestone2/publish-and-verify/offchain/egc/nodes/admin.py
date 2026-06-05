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
        key_pair: KeyPair,

        # TODO ipfs (kubo)
    ):
        LOG.debug('Admin.__init__')
        super().__init__(
            role='admin',
            role_index=1,
            election=election,
            key_pair=key_pair
        )

    # TODO how to refactor this for admin vs subchannels?
    def _build_post_tx(
            self,
            new_records: List[PublicRecord],
            new_phase: Optional[ElectionPhase] = None,
        ) -> TransactionBuilder:

        LOG.debug('Admin._build_post_tx')

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

        # We need the in_value unmutated because PyCardano will use it to
        # calculate the inputs, so create a separate out_value to top up.
        in_value = in_utxo.output.amount
        out_value = Value.from_primitive(in_value.to_primitive())  # deep copy

        out_utxo = TransactionOutput(
            address=self.election.address,
            amount=out_value,
            datum=out_datum,
        )

        LOG.debug('out_utxo before top-up: %s' % pformat(out_utxo))
        top_up_to_min_ada(out_utxo)
        LOG.debug('out_utxo after top-up: %s' % pformat(out_utxo))

        redeemer = Redeemer(data=PostPublicRecords())

        txb = (
            TransactionBuilder(OGMIOS_CTX)
            .add_script_input(in_utxo, script=self.election.script.spend_script, redeemer=redeemer)
            .add_output(out_utxo)
        )
        txb.required_signers = [self.publisher.key_pair.vkh] # TODO remove?

        return txb

    # TODO should this go in the base class?
    def post_public_records(
            self,
            new_records: List[PublicRecord],
            new_phase: Optional[ElectionPhase] = None,
        ) -> Transaction:
        LOG.debug('Admin.post_public_records')
        txb = self._build_post_tx(new_records, new_phase)
        tx  = self.publisher.sign_and_submit(tx)
        return tx
