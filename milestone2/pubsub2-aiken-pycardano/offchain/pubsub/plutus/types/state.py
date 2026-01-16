from dataclasses import dataclass
from pycardano import PlutusData
from typing import List

@dataclass
class PubsubState(PlutusData):
    CONSTR_ID = 0
    publisher: bytes  # VerificationKeyHash - 28 bytes
    cids: List[bytes] # CIDv1 just converts str <--> bytes now
    seq: int # index for double checking nothing is missed (unused so far)
