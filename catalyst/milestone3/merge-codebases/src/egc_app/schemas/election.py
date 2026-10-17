from typing import Annotated, Any
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import core_schema
from pycardano import VerificationKeyHash
from egc import ElectionConfig
from .wallet import SigningKeyType

# TODO move to a util file?
class _VerificationKeyHashPydantic:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(v: Any) -> VerificationKeyHash:
            if isinstance(v, VerificationKeyHash):
                return v
            return VerificationKeyHash.from_cbor(v)  # hex str or bytes

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda k: k.to_cbor_hex(), return_schema=core_schema.str_schema()
            ),
        )

VerificationKeyHashType = Annotated[VerificationKeyHash, _VerificationKeyHashPydantic]

class ElectionSubscribe(BaseModel):
    config: ElectionConfig

class ElectionCreate(BaseModel):
    funder_sk: SigningKeyType
    admin_vkh: VerificationKeyHashType
    admin_ada: int = 100
