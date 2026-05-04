from election import publisher as ep
from pycardano import UTxO

# TODO how should this relate to the eventual Quart server? guess it's the backend/model?
# TODO plan that all out roughly before continuing to code here

class Admin:
    def __init__(
        self,
        keys_dir: Path,
        ogmios: OgmiosV6ChainContext,
        # TODO ipfs (kubo)
    ):
        self.keys_dir = keys_dir
        self.publisher = None
        self.subscriber = None
        self.ogmios = ogmios

    def _init_publisher(self, oneshot_utxo: UTxO):
        """Delayed init for publisher because we need to know the one-shot UTxO."""
        script = ElectionScript(oneshot_utxo)
        self.publisher = ep.Publisher(
            role="admin",
            index=1,
            keys_dir=self.keys_dir,
            script=script,
            ogmios=self.ogmios
        )

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        script = ElectionScript(oneshot_utxo)
        self.subscriber = es.Subscriber(script)

    def init_election(self):
        """Create admin STT and run delayed init functions."""
        oneshot_utxo = ... # TODO write this
        kupo_args = ... # TODO write this
        self._init_publisher(oneshot_utxo)
        self._init_subscriber(kupo_args)
        # TODO write this
