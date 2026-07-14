import time
from pathlib import Path
from typing import List, Optional
from ..core import *
from .observer import ObserverNode
from pycardano import *
from dataclasses import replace
import logging

LOG = logging.getLogger(__name__)

class VerifierNode(ObserverNode):

    def __init__(
        self,

        # For deriving the ChannelId
        role_index: int,

        election: ElectionContext,

        # No need for keys_dir or key_name if you pass an existing wallet.
        # You can also omit them without passing wallet, in which case a new
        # Wallet will generated based on the role + index and saved in the
        # default dir. This logic is handled by the Publisher.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

    ):
        LOG.debug('VerifierNode.__init__')
        super().__init__(
            role       = 'verifier',
            role_index = role_index,
            election   = election,
            wallet     = wallet,
            keys_dir   = keys_dir,
            key_name   = key_name,
        )


