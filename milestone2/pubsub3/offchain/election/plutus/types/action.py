from dataclasses import dataclass
from typing import ClassVar, Dict, Type
from pycardano import PlutusData, RawPlutusData

# These should be kept in sync with onchain/validators/election/action.ak!

# Apparently there's no built in way in PyCardano to decode a superclass; you
# have to know the concrete class first or try each of them. This is a first
# attempt at working around that. It registers subclasses as long as they have a
# CONSTR_ID and picks the correct one to decode. It can also be used as a union type.
#
# TODO if it works well, consider contributing it upstream
#
@dataclass
class ElectionAction(PlutusData):
    _registry: ClassVar[Dict[int, Type["ElectionAction"]]] = {}
    CONSTR_ID: ClassVar[int]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls is not ElectionAction and hasattr(cls, "CONSTR_ID"):
            constr_id = cls.CONSTR_ID
            if constr_id in ElectionAction._registry:
                raise ValueError(
                    f"Duplicate CONSTR_ID {constr_id} for {cls} "
                    f"and {ElectionAction._registry[constr_id]}"
                )
            ElectionAction._registry[constr_id] = cls

    @classmethod
    def decode(cls, cbor: bytes) -> "ElectionAction":
        raw = RawPlutusData.from_cbor(cbor)
        tag = raw.data  # CBORTag(121/122/123, <fields>)
        if not isinstance(tag.tag, int):
            raise ValueError(f"Unexpected tag type: {type(tag.tag)}")

        constr_id = tag.tag - 121  # 121 -> 0, 122 -> 1, 123 -> 2, ...

        subcls = cls._registry.get(constr_id)
        if subcls is None:
            raise ValueError(f"Unknown ElectionAction CONSTR_ID: {constr_id}")

        # Call original PlutusData.from_cbor on the subclass to avoid recursion
        return PlutusData.from_cbor.__func__(subcls, cbor)

    @classmethod
    def decode_hex(cls, cbor_hex: str) -> "ElectionAction":
        return cls.decode(bytes.fromhex(cbor_hex))


# Concrete types defined after base

@dataclass
class InitElection(ElectionAction):
    CONSTR_ID = 0

@dataclass
class AddSubChannels(ElectionAction):
    CONSTR_ID = 1
    channels: List[bytes] # ChannelId == ByteArray

@dataclass
class AdvancePhase(ElectionAction):
    CONSTR_ID = 2

@dataclass
class EndElection(ElectionAction):
    CONSTR_ID = 3

@dataclass
class RmSubChannels(ElectionAction):
    CONSTR_ID = 4
    channels: List[bytes] # ChannelId == ByteArray

@dataclass
class RebalanceFunds(ElectionAction):
    CONSTR_ID = 5
    channels: List[bytes] # ChannelId == ByteArray

@dataclass
class EndElection(ElectionAction):
    CONSTR_ID = 6

@dataclass
class BurnTestTokens(ElectionAction):
    CONSTR_ID = 7
