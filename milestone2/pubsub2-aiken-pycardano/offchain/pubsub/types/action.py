from .cid import CIDv1
from dataclasses import dataclass
from pycardano import PlutusData
from typing import List

@dataclass
class PubsubAction(PlutusData):
    "Superclass to use as a union type"

@dataclass
class PsOpen(PubsubAction):
    """
    Examples:
        >>> open_action = PsOpen()
    """
    CONSTR_ID = 0

@dataclass
class PsPublish(PubsubAction):
    """
    Examples:
        >>> TODO fill in
    """
    CONSTR_ID = 1
    cids: List[CIDv1]

# TODO remove?
# @dataclass
# class PsCollect(PubsubAction):
#     CONSTR_ID = 2

@dataclass
class PsClose(PubsubAction):
    """
    Examples:
        >>> close_action = PsClose()
    """
    CONSTR_ID = 2
