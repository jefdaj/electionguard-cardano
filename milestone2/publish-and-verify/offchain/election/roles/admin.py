from election import publisher as ep
from election.plutus.script import ElectionScript
from pycardano import UTxO
from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext

# TODO how should this relate to the eventual Quart server? guess it's the backend/model?

class Admin:
    def __init__(
        self,
        keys_dir: Path,
        # TODO pass once using more than one: ogmios: OgmiosV6ChainContext,
        # TODO ipfs (kubo)
    ):
        self.keys_dir = keys_dir
        self.publisher = None
        self.subscriber = None
        # self.ogmios = OGMIOS_CTX

    def _init_publisher(self):
        """Delayed init for publisher because we need to know the one-shot UTxO."""
        # script = ElectionScript(oneshot_utxo)
        self.publisher = ep.ElectionPublisher(
            role="admin",
            index=1,
            keys_dir=self.keys_dir,
            # script=script,
            # ogmios=self.ogmios
        )

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        # script = ElectionScript(oneshot_utxo)
        self.subscriber = es.Subscriber(self.publisher.script)

    def init_election(self):
        """Create admin STT and run delayed init functions."""
        oneshot_utxo = ... # TODO write this
        kupo_args = ... # TODO write this
        self._init_publisher(oneshot_utxo)
        self._init_subscriber(kupo_args)
        # TODO write this
        return kupo_args
