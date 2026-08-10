from pydantic import BaseModel

class IpfsNodeOut(BaseModel):
    peer_id: str
    addr_hints: list[str]

class IpfsNodesOut(BaseModel):
    channel_nodes: dict[str, IpfsNodeOut]
