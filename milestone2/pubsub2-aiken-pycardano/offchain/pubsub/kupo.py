from dataclass import dataclass
from typing import Callable

@dataclass
class KupoConfig:
    since_slot: int  # For kupo --since
    since_block: str # For kupo --since
    until_slot: Optional[int] # For kupo --until, to prevent open-ended scans during tests
    policy_id: str here too? # For kupo --match TODO remove?

# TODO is this how you define a type?
# TODO can the response type be more specific than dict?
# Handles a single kupo match response json obj.
# I think kupo yields an iterator of these? TODO check that
KupoMatchCallback = Callable[[dict], None]

class KupoSubscriberThread:
    """
    Runs kupo and feeds matches to a callback.
    Note that since_slot and since_block should be figured out *before* deploying the contract,
    to be sure the indexed range will include the first transaction.
    until_slot prevents open-ended scanning during tests.
    """

    def __init__(
            self,
            config: KupoConfig,
            on_match: KupoMatchCallback
        ):
        self.config = config
        self.on_match = on_match

# TODO paste/move all of ../kupo.py here and start from it
