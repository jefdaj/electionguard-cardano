# from typing import List
from dataclasses import dataclass
from pycardano import PlutusData

# TODO validation? at least constrain length
CID = bytes

@dataclass
class PubsubAction(PlutusData):
    "Superclass to use as a union type"

@dataclass
class PsOpen(PubsubAction):
    CONSTR_ID = 0

# TODO put back after building out the test framework with just open + close
# @dataclass
# class PsPublish(PubsubAction):
#     CONSTR_ID = 1
#     cids: List[bytes]

# TODO remove?
# @dataclass
# class PsCollect(PubsubAction):
#     CONSTR_ID = 2

@dataclass
class PsClose(PubsubAction):
    CONSTR_ID = 1 # TODO will be 2 once PsPublish is added
