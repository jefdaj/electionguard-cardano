from pathlib import Path
from ..core import *
from pycardano import *
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

        # for creating the Subcscriber
        self.role = "admin"
        self.role_index = 1

        super().__init__(election=election, key_pair=key_pair)

    def _build_post_tx(
            self,
            new_records: List[PublicRecord],
            new_phase: Optional[ElectionPhase] = None,
        ) -> TransactionBuilder:
        txb = None
        return txb

    def post_public_records(
            self,
            new_records: List[PublicRecord],
            new_phase: Optional[ElectionPhase] = None,
        ) -> Transaction:
        txb = self._build_post_tx(new_records, new_phase)
        tx  = self.publisher.sign_and_submit(tx)
        return tx
