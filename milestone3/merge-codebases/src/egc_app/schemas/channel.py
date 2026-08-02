from pydantic import BaseModel, field_validator
from typing import Annotated, Optional
from egc import is_valid_role, is_valid_channel_str

class ChannelAwait(BaseModel):
    role: str

    @field_validator('role')
    def check_role(cls, v: str) -> str:
        assert is_valid_role(v)
        return v

class ChannelAwaitOut(BaseModel):
    channel_str: str

    @field_validator('channel_str')
    def check_role(cls, v: str) -> str:
        assert is_valid_channel_str(v)
        return v
