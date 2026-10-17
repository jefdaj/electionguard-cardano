import time
from pathlib import Path
from typing import List, Optional
from ..core import *
from .verifier import VerifierNode
from pycardano import *
from dataclasses import replace
import logging

LOG = logging.getLogger(__name__)

class DeviceNode(VerifierNode):

    def __init__(
        self,

        # Where to keep records_to_post, records_fetched, and other files as needed.
        private_dir: Path,

        # For deriving the ChannelId
        role_index: int,

        election_cfg: ElectionConfig,

        # No need for keys_dir or key_name if you pass an existing wallet.
        # You can also omit them without passing wallet, in which case a new
        # Wallet will generated based on the role + index and saved in the
        # default dir. This logic is handled by the Publisher.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

    ):
        LOG.debug('DeviceNode.__init__')
        super().__init__(
            private_dir = private_dir,
            role       = 'device',
            role_index = role_index,
            election_cfg = election_cfg,
            wallet     = wallet,
            keys_dir   = keys_dir,
            key_name   = key_name,
        )


