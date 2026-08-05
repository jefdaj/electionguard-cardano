from pydantic import BaseModel, field_validator
from typing import Annotated, Optional

class RecordsListOut(BaseModel):
    records: list[PublicRecordMetadata]
