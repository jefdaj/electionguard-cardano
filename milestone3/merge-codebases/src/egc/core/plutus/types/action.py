# Should be kept in sync with onchain/validators/election/action.ak
# Note that order is important! CONSTR_IDs must all match.

from dataclasses import dataclass
from typing import List, Union
from pycardano import PlutusData
from .channel_id import ChannelIdMixin
import cbor2
from typing import get_args, Union, Type


### Admin actions spending admin channel ###

@dataclass
class InitElection(PlutusData):
    CONSTR_ID = 0

@dataclass
class AddSubChannels(ChannelIdMixin, PlutusData):
    CONSTR_ID = 1
    channels: List[bytes]

@dataclass
class AdvancePhase(PlutusData):
    CONSTR_ID = 2

@dataclass
class EndElection(PlutusData):
    CONSTR_ID = 3


### Admin actions spending multiple channels ###

@dataclass
class RmSubChannels(ChannelIdMixin, PlutusData):
    CONSTR_ID = 4
    channels: List[bytes]

@dataclass
class RebalanceFunds(ChannelIdMixin, PlutusData):
    CONSTR_ID = 5
    channels: List[bytes]


### Single-channel actions for anyone ###

@dataclass
class PostPublicRecords(PlutusData):
    CONSTR_ID = 6


### Actions to remove for production use ###

@dataclass
class BurnTestTokens(PlutusData):
    CONSTR_ID = 7


ElectionAction = Union[
  InitElection,
  AddSubChannels,
  AdvancePhase,
  EndElection,
  RmSubChannels,
  RebalanceFunds,
  PostPublicRecords,
  BurnTestTokens,
]


# TODO move since now it's also used with PublicRecordMetadata
def decode_plutusdata_union(union_type, cbor_hex: str) -> PlutusData:
    """Decode a top-level union. Apparently pycardano has this logic, but only
    for nested types inside a larger PlutusData wrapper type. Maybe it's worth
    opening an issue about exposing for union types directly?"""

    dispatch = {cls.CONSTR_ID: cls for cls in get_args(union_type)}
    raw = bytes.fromhex(cbor_hex)
    tag = cbor2.loads(raw)  # cbor2.CBORTag

    if 121 <= tag.tag <= 127:
        constr_id = tag.tag - 121
    elif 1280 <= tag.tag <= 1400:
        constr_id = tag.tag - 1280 + 7
    elif tag.tag == 102:
        constr_id = tag.value[0]  # [index, fields]
    else:
        raise ValueError(f"Not a Plutus constr tag: {tag.tag}")

    cls = dispatch.get(constr_id)
    if cls is None:
        raise ValueError(f"Unknown CONSTR_ID {constr_id} for ElectionAction")
    return cls.from_cbor(raw)


def decode_action(redeemer_str):
    return decode_plutusdata_union(ElectionAction, redeemer_str)
