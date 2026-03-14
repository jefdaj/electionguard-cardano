# Should be kept in sync with onchain/validators/election/action.ak

from dataclasses import dataclass
from typing import List, Union
from pycardano import PlutusData
from .channel_id import ChannelId

@dataclass
class InitElection(PlutusData):
    CONSTR_ID = 0

@dataclass
class AddSubChannels(PlutusData):
    CONSTR_ID = 1
    channels: List[ChannelId]

@dataclass
class AdvancePhase(PlutusData):
    CONSTR_ID = 2

@dataclass
class EndElection(PlutusData):
    CONSTR_ID = 3

@dataclass
class RmSubChannels(PlutusData):
    CONSTR_ID = 4
    channels: List[ChannelId]

@dataclass
class RebalanceFunds(PlutusData):
    CONSTR_ID = 5
    channels: List[ChannelId]

@dataclass
class PostPublicRecords(PlutusData):
    CONSTR_ID = 6

@dataclass
class EndElection(PlutusData):
    CONSTR_ID = 7

@dataclass
class BurnTestTokens(PlutusData):
    CONSTR_ID = 8

ElectionAction = Union[
  InitElection,
  AddSubChannels,
  AdvancePhase,
  EndElection,
  RmSubChannels,
  RebalanceFunds,
  PostPublicRecords,
  EndElection,
  BurnTestTokens,
]
