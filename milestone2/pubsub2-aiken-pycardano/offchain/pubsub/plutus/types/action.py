from dataclasses import dataclass
from typing import ClassVar, Dict, Type, List
from pycardano import PlutusData, RawPlutusData

# Apparently there's no built in way in PyCardano to decode a superclass; you
# have to know the concrete class first or try each of them. This is a first
# attempt at working around that. It registers subclasses as long as they have a
# CONSTR_ID and picks the correct one to decode. It can also be used as a union type.
#
# TODO if it works well, consider contributing it upstream
#
@dataclass
class PubsubAction(PlutusData):
    _registry: ClassVar[Dict[int, Type["PubsubAction"]]] = {}
    CONSTR_ID: ClassVar[int]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls is not PubsubAction and hasattr(cls, "CONSTR_ID"):
            cid = cls.CONSTR_ID
            if cid in PubsubAction._registry:
                raise ValueError(
                    f"Duplicate CONSTR_ID {cid} for {cls} "
                    f"and {PubsubAction._registry[cid]}"
                )
            PubsubAction._registry[cid] = cls

    @classmethod
    def decode(cls, cbor: bytes) -> "PubsubAction":
        raw = RawPlutusData.from_cbor(cbor)
        tag = raw.data  # CBORTag(121/122/123, <fields>)
        if not isinstance(tag.tag, int):
            raise ValueError(f"Unexpected tag type: {type(tag.tag)}")

        constr_id = tag.tag - 121  # 121 -> 0, 122 -> 1, 123 -> 2, ...

        subcls = cls._registry.get(constr_id)
        if subcls is None:
            raise ValueError(f"Unknown PubsubAction CONSTR_ID: {constr_id}")

        # Call original PlutusData.from_cbor on the subclass to avoid recursion
        return PlutusData.from_cbor.__func__(subcls, cbor)

    @classmethod
    def decode_hex(cls, cbor_hex: str) -> "PubsubAction":
        return cls.decode(bytes.fromhex(cbor_hex))


# Concrete types defined after base

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
    cids: List[bytes] # CIDv1 just converts str <--> bytes now

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
