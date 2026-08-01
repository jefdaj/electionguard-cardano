from pydantic import BaseModel
from typing import Optional

class ChannelAwait(BaseModel):
    role: str

class ChannelAwaitOut(BaseModel):
    channel_str: str
