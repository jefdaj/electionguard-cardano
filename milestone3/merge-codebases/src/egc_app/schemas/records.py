from pydantic import BaseModel, field_validator
from typing import Annotated, Optional
from egc import PublicRecordMetadata

class RecordsListOut(BaseModel):
    records: list[PublicRecordMetadata] # if too many issues, send path and convert in cli
    # records: list[str]
