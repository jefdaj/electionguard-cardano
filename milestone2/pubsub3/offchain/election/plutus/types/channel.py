# Should be kept in sync with onchain/validators/election/types/channel.ak

from dataclasses import dataclass
from pycardano import PlutusData
from typing import List, Union
from .cid import CID, CIDHelper
from .phase import ElectionPhase

# @dataclass
# class PubsubState(PlutusData):
#     CONSTR_ID = 0
#     publisher: bytes  # VerificationKeyHash - 28 bytes
#     cids: List[bytes] # CID just converts str <--> bytes now
#     seq: int # index for double checking nothing is missed (unused so far)
# 
#     def __repr__(self):
#         cids_str = [CIDHelper.to_string(cid) for cid in self.cids]
#         return (
#             'PubsubState('
#             f'publisher={self.publisher.hex()}, '
#             f'cids={cids_str}, '
#             f'seq={self.seq})'
#         )


# ==================
# ChannelId
# ==================

type ChannelId = bytes


# ==================
# ChannelState
# ==================

@dataclass
class AdminChannelState(PlutusData):
    CONSTR_ID = 0
    admin: bytes  # VerificationKeyHash
    subchannels: List[ChannelId]
    new_records: List[PublicRecord]
    phase: ElectionPhase
    seq: int

    def __repr__(self):
        subchannels_str = [ch.hex() for ch in self.subchannels]
        records_repr = [
            f"{type(r.metadata).__name__}(cid={CIDv1Helper.to_string(r.cid)})"
            for r in self.new_records
        ]
        return (
            'AdminChannelState('
            f'admin={self.admin.hex()}, '
            f'subchannels={subchannels_str}, '
            f'new_records={records_repr}, '
            f'phase={repr(self.phase)}, '
            f'seq={self.seq})'

@dataclass
class SubChannelState(PlutusData):
    CONSTR_ID = 0
    channel_id: ChannelId
    publisher: bytes   # VerificationKeyHash
    new_records: List[PublicRecord]
    seq: int

    def __repr__(self):
        records_repr = [
            f"{type(r.metadata).__name__}(cid={CIDv1Helper.to_string(r.cid)})"
            for r in self.new_records
        ]
        return (
            'SubChannelState('
            f'channel_id={self.channel_id.hex()}, '
            f'publisher={self.publisher.hex()}, '
            f'new_records={records_repr}, '
            f'seq={self.seq})'
        )

@dataclass
class AdminChannel(PlutusData):
    CONSTR_ID = 0
    state: AdminChannelState

    def __repr__(self):
        return f'AdminChannel({repr(self.state)})'

@dataclass
class SubChannel(PlutusData):
    CONSTR_ID = 1
    state: SubChannelState

    def __repr__(self):
        return f'SubChannel({repr(self.state)})'

ChannelState = Union[AdminChannel, SubChannel]
