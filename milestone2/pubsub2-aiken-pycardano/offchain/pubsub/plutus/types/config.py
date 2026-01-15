from dataclasses import dataclass
from pycardano import PlutusData

# TODO rename PubsubConfig -> PubsubState? ChannelState?

@dataclass
class PubsubConfig(PlutusData):
    CONSTR_ID = 0
    publisher: bytes  # VerificationKeyHash - 28 bytes
