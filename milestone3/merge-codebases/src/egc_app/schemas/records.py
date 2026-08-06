from pydantic import BaseModel, field_validator
from egc import PublicRecordMetadata, decode_metadata

from typing import Annotated, Any, Optional
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import core_schema

# TODO move to a util file?
class _PublicRecordMetadataPydantic:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(v: Any) -> PublicRecordMetadata:
            if isinstance(v, PublicRecordMetadata):
                return v
            return decode_metadata(v)

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda k: k.to_cbor_hex(), return_schema=core_schema.str_schema()
            ),
        )

PublicRecordMetadataType = Annotated[PublicRecordMetadata, _PublicRecordMetadataPydantic]


class RecordsListOut(BaseModel):
    records: list[PublicRecordMetadataType]


class RecordsDrop(BaseModel):
    indexes_to_drop: list[int]


class RecordsPost(BaseModel):
    indexes_to_post: list[int] # auto-select if empty
    min_size:        int
    advance_phase:   Optional[str] # TODO parse?
