from dataclasses import dataclass
from pycardano import PlutusData

@dataclass
class PubsubConfig(PlutusData):
    CONSTR_ID = 0
    publisher: bytes  # VerificationKeyHash - 28 bytes
