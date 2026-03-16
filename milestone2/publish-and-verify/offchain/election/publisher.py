from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext, SigningKey, Transaction, TransactionBuilder
from time import sleep
from typing import List, Optional

# from .ogmios import query_network_tip_sync
# from .wallet import addr_for_signing_key, vkh_for_signing_key
# from .plutus import (
#     pick_oneshot_utxo,
#     PubsubScript, PubsubAction, PsOpen, PsPublish, PsClose,
#     build_psopen_tx, build_pspublish_tx, build_psclose_tx
# )

class Publisher:

    def __init__(
        self,
        ogmios: OgmiosV6ChainContext,
        # TODO generate a set of these: publisher_signing_key: SigningKey,
        # TODO ipfs_client
    ):
        self.ogmios = ogmios
        self.publisher_signing_key = publisher_signing_key
        self.publisher_verification_key_hash = vkh_for_signing_key(self.publisher_signing_key)
        self.publisher_address = addr_for_signing_key(self.publisher_signing_key)
        self.oneshot_utxo = pick_oneshot_utxo(ogmios, self.publisher_address)
        self.pubsub_script = PubsubScript(self.oneshot_utxo)
        self.channel_state: Optional[str] = None # TODO formalize a type
        self.published_cids = []
        self.tip_before_open: Optional[tuple[int, str]] = None


