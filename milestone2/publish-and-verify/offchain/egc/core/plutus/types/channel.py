# Should be kept in sync with onchain/validators/election/types/channel.ak

from .channel_id import ChannelId, ChannelIdHelper, ADMIN_CHANNEL_ID
# from .ipfs_cid import IpfsCid, IpfsCidHelper
from .phase import ElectionPhase
from .record import PublicRecord
from dataclasses import dataclass
from pycardano import PlutusData, Network, VerificationKeyHash, Address
from typing import List, Union, TYPE_CHECKING

# TODO rewrite these to use __repr__ rather than __str__ and standardize on JSON?

@dataclass
class AdminChannelState(PlutusData):
    CONSTR_ID = 0
    admin: bytes  # VerificationKeyHash
    subchannels: List[bytes]
    new_records: List[PublicRecord]
    phase: ElectionPhase
    seq: int

    def __str__(self):
        # TODO are these missing their list brackets?
        subchannels_str = [ch.hex() for ch in self.subchannels]
        records_str = [str(r) for r in self.new_records] # TODO is this right?
        return (
            'AdminChannelState('
            f'admin={self.admin.hex()}, '      # TODO clean up to avoid bytes.fromhex
            f'subchannels={subchannels_str}, ' # TODO clean up to avoid bytes.fromhex
            f'new_records={records_str}, '
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

    def __str__(self):
        records_str = [str(r) for r in self.new_records] # TODO is this right?
        return (
            'SubChannelState('
            f'channel_id={self.channel_id.hex()}, ' # TODO clean up to avoid bytes.fromhex
            f'publisher={self.publisher.hex()}, '   # TODO clean up to avoid bytes.fromhex
            f'new_records={records_str}, '
            f'seq={self.seq})'
        )

@dataclass
class AdminChannel(PlutusData):
    CONSTR_ID = 0
    state: AdminChannelState

    def __str__(self):
        return f'AdminChannel({str(self.state)})'

@dataclass
class SubChannel(PlutusData):
    CONSTR_ID = 1
    state: SubChannelState

    def __str__(self):
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
