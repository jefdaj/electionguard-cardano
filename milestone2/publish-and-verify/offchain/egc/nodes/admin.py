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
        (utxo, st) = self.state() # TODO error handling here?
        LOG.debug('st: %s' % pformat(st))
        cont = AdminChannel(state=replace(
            st,
            new_records = new_records,
            phase = st.phase if new_phase is None else new_phase,
            seq = st.seq + 1,
        ))
        LOG.debug('cont: %s' % pformat(cont))
        txb = (
            TransactionBuilder(OGMIOS_CTX, mint=assets)
            .add_input(script.oneshot_utxo)
            .add_output(stt_output)
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
