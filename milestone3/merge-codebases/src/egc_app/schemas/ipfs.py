from pydantic import BaseModel

class IpfsNodeOut(BaseModel):
    peer_id: str
    addr_hints: list[str]

class IpfsNodesOut(BaseModel):
    own_node: IpfsNodeOut
    channel_nodes: dict[str, IpfsNodeOut]
