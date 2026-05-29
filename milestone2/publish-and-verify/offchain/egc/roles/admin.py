from election import publisher as ep
from election.plutus import script as es
from election.ogmios import OGMIOS_CTX
from election import wallet as ew
from pycardano import UTxO
from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext
import logging

log = logging.getLogger(__name__)

# TODO how should this relate to the eventual Quart server? guess it's the backend/model?

# def init_election(admin, keys_dir=ew.DEF_KEYS_DIR, main_wallet_name='main'):
#     """This is a weird step because it needs to be done by the main wallet, not the admin."""
#     # TODO should this create the admin rather than taking it as an arg?
#     main_addr = load_wallet_addr(keys_dir=keys_dir, name=main_wallet_name)
#     oneshot_utxo = es.pick_oneshot_utxo(OGMIOS_CTX, main_addr)
#     script = ElectionScript(oneshot_utxo)
#     admin._init_publisher(script)
#     # admin_addr = admin.publisher.address
#     return admin.init_election()

# TODO same for final election close/burn?

class Admin:
    def __init__(
        self,
        keys_dir: Path,
        # TODO pass once using more than one: ogmios: OgmiosV6ChainContext,
        # TODO ipfs (kubo)
    ):
        log.debug('Admin.__init__')
        self.keys_dir = keys_dir
        self.publisher = None
        self.subscriber = None
        self.ogmios = OGMIOS_CTX

    def _init_publisher(self, script):
        """Delayed init for publisher because we need to know the one-shot UTxO."""
        log.debug('Admin._init_publisher')
        self.publisher = ep.ElectionPublisher(
            role="admin",
            index=1,
            keys_dir=self.keys_dir,
            script=script,
            # ogmios=self.ogmios
        )

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        log.debug('Admin._init_subcsriber')
        # script = ElectionScript(oneshot_utxo)
        self.subscriber = es.Subscriber(self.publisher.script)

    def init_election(self):
        """Create admin STT and run delayed init functions."""
        log.debug('Admin._init_election')
        # oneshot_utxo = ... # TODO write this
        # self._init_publisher(oneshot_utxo)
        # kupo_args = ... # TODO write this
        # TODO write this: self._init_subscriber(kupo_args)
        # return kupo_args
