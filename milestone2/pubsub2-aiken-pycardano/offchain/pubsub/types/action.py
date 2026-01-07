from .cid import CIDv1
from dataclasses import dataclass
from pycardano import PlutusData

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

# TODO put back after building out the test framework with just open + close
# @dataclass
# class PsPublish(PubsubAction):
#     """
#     Examples:
#         >>> publish_action = PubsubAction.ps_publish([b'cid1', b'cid2'])
#     """
#     CONSTR_ID = 1
#     cids: List[CIDv1]

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
    CONSTR_ID = 1 # TODO will be 2 once PsPublish is added
