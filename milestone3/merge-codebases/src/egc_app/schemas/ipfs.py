from pydantic import BaseModel
from typing import Optional

class IpfsNodeOut(BaseModel):
    peer_id: str
    addr_hints: list[str]

class IpfsNodesOut(BaseModel):
    own_node: Optional[IpfsNodeOut]
    channel_nodes: dict[str, IpfsNodeOut]
