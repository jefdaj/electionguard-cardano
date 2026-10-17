from typing import Annotated, Any
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import core_schema
from pycardano import SigningKey

# TODO move to a util file?
class _SigningKeyPydantic:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(v: Any) -> SigningKey:
            if isinstance(v, SigningKey):
                return v
            return SigningKey.from_cbor(v)  # hex str or bytes

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda k: k.to_cbor_hex(), return_schema=core_schema.str_schema()
            ),
        )

SigningKeyType = Annotated[SigningKey, _SigningKeyPydantic]

class WalletLoadOrCreate(BaseModel):
    sk_or_desc: SigningKeyType|str # if str, generate using description
