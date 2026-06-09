from pathlib import Path
from pycardano import *

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
            self.subscriber = ElectionSubscriber(config=sub_cfg)
            self.subscriber.start()

    def channel_id(self) -> ChannelId:
        return self.publisher.channel_id()

    def state(self) -> Optional[Tuple[UTxO, ChannelState]]:
        try:
            return self.subscriber.states[self.channel_id()] # .state
        except KeyError:
            # no state yet
            # TODO should this be a warning?
            return None

    def election_phase(self) -> Optional[ElectionPhase]:
        try:
            (_, state) = self.subscriber.states[ADMIN_CHANNEL_ID]
            return state.state.phase
        except KeyError:
            # no init_election tx published yet
            # TODO should this be an error? warning?
            return None

    # TODO wait_for_confirmation method that uses both pub and sub state?
