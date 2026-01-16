from dataclasses import dataclass
from pycardano import PlutusData

# TODO rename PubsubConfig -> PubsubState? ChannelState?
# TODO any need for something like the fancy PubsubAction superclass here?

@dataclass
class PubsubConfig(PlutusData):
    CONSTR_ID = 0
    publisher: bytes  # VerificationKeyHash - 28 bytes
