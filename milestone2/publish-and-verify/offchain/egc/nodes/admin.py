from pathlib import Path
from ..core import *
from pycardano import *
import logging

LOG = logging.getLogger(__name__)

# TODO how should this relate to the eventual Quart server? guess it's the backend/model?

class Admin:
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

        self.key_pair = key_pair
        self.election = election

        self.publisher = ElectionPublisher(
            role="admin",
            role_index=1,
            key_pair=self.key_pair,
        )

        sub_cfg = SubscriberConfig.from_election(self.election)
        self.subscriber = ElectionSubscriber(config=sub_cfg)
        self.subscriber.start()
