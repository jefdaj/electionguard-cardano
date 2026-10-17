# Should be kept in sync with onchain/validators/election/types/channel.ak

from .channel_id import *
from .phase import ElectionPhase
from .record import PublicRecord
from dataclasses import dataclass
from pycardano import PlutusData, Network, VerificationKeyHash, Address
from typing import List, Union, TYPE_CHECKING

# TODO rewrite these to use __str__ rather than __repr__ and standardize on JSON?

@dataclass
class AdminChannelState(PlutusData):
    CONSTR_ID = 0
    admin: bytes  # VerificationKeyHash
    subchannels: List[bytes]
    new_records: List[PublicRecord]
    phase: ElectionPhase
    seq: int

    def __repr__(self):
        # TODO are these missing their list brackets?
        sub_strs = self.subchannels
        records_str = ', '.join([str(r) for r in self.new_records])
        return (
            'AdminChannelState('
            f"admin='{self.admin.hex()}', "     # TODO clean up to avoid bytes.fromhex
            f'subchannels={self.subchannels}, ' # TODO clean up to avoid bytes.fromhex
            f'new_records=[' + records_str + '], '
            f'phase={str(self.phase)}, '
            f'seq={self.seq})'
        )

@dataclass
class SubChannelState(PlutusData):
    CONSTR_ID = 0
    channel_id: bytes
    publisher: bytes   # VerificationKeyHash
    new_records: List[PublicRecord]
    seq: int

    def __repr__(self):
        ch_str = channel_id_to_string(self.channel_id)
        records_str = ', '.join([str(r) for r in self.new_records])
        return (
            'SubChannelState('
            f'channel_id={self.channel_id}, '
            f"publisher='{self.publisher.hex()}', "   # TODO clean up to avoid bytes.fromhex
            f'new_records=[' + records_str + '], '
            f'seq={self.seq})'
        )

@dataclass
class AdminChannel(PlutusData):
    CONSTR_ID = 0
    state: AdminChannelState

    def __repr__(self):
        return f'AdminChannel({str(self.state)})'

@dataclass
class SubChannel(PlutusData):
    CONSTR_ID = 1
    state: SubChannelState

    def __repr__(self):
        return f'SubChannel({str(self.state)})'

ChannelState = Union[AdminChannel, SubChannel]

def channel_id_from_state(state: ChannelState) -> ChannelId:
    if isinstance(state, AdminChannel):
        return ADMIN_CHANNEL_ID
    else:
        return state.state.channel_id

def publisher_address(state: ChannelState, network=Network.TESTNET) -> Address:
    "Mainly to help return collateral in test fixtures."
    # TODO later, don't assume testnet
    if isinstance(state, AdminChannel):
        vkh_bytes = state.state.admin
    else:
        vkh_bytes = state.state.publisher
    vkh = VerificationKeyHash(vkh_bytes)
    addr = Address(payment_part=vkh, network=network)
    return addr
