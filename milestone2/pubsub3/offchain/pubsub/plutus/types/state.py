from dataclasses import dataclass
from pycardano import PlutusData
from typing import List
from .cid import CIDv1

@dataclass
class PubsubState(PlutusData):
    CONSTR_ID = 0
    publisher: bytes  # VerificationKeyHash - 28 bytes
    cids: List[bytes] # CIDv1 just converts str <--> bytes now
    seq: int # index for double checking nothing is missed (unused so far)

    def __repr__(self):
        cids_str = [CIDv1.to_string(cid) for cid in self.cids]
        return (
            'PubsubState('
            f'publisher={self.publisher.hex()}, '
            f'cids={cids_str}, '
            f'seq={self.seq})'
        )
