# Should be kept in sync with onchain/validators/election/action.ak
# Note that order is important! CONSTR_IDs must all match.

from dataclasses import dataclass
from typing import List, Union
from pycardano import PlutusData
from .channel_id import ChannelIdMixin


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
