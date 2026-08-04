# TODO rename funder -> treasury? maybe later when treasuries involved

from pathlib import Path
from typing import List
from pprint import pformat
from datetime import datetime

from pycardano import *
from ..core import *
# from .admin import *

# careful, admin and pycardano can both shadow this
import logging

LOG = logging.getLogger(__name__)


# TODO should observer be the base ElectionNode class rather than inheriting from it?
class ObserverNode(ElectionNode):
    """Besides observing an election (subscribing + streaming events),
    Observers can also:
    1. request an official role from the admin of an existing election
    2. fund a new election, becoming the funder and designating an admin
    3. become the admin of a new election using a temporary funder

    If only observing though, they don't need a wallet.
    """

    def __init__(
        self,

        # Where to keep records_to_post, records_fetched, and other files as needed.
        private_dir: Path,

        # Observers don't have channels, so they don't officially have an index.
        # But it's still useful for distinguishing state dirs during tests.
        role: str = 'observer',
        role_index: int = 1, # TODO option to have other indexes for tests

        # No election context is needed at init time; it's assumed you will
        # create or subscribe to one separately later.

        # If you pass a wallet it'll be used directly. If you pass keys_dir +
        # key_name, a wallet will be generated based on the role_index in the
        # default dir. If you don't pass either you won't have to bother with a
        # wallet, until you want to request/create an official role.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

    ):
        LOG.debug('Observer.__init__')

        # No election here because the Observer has to exist in order to create
        # it. And with no election, the ElectionNode class won't init a
        # subscriber yet either.
        super().__init__(
            private_dir=private_dir,
            role=role,
            role_index=role_index,
            wallet=wallet,
        )
