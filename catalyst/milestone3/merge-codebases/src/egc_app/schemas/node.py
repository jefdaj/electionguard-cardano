from pydantic import BaseModel

class NodeStatusOut(BaseModel):
    # server_status: str = "ok"
    ipfs_peers: int
    ipfs_bw_bs: int
    # TODO cardano sync progress
    # TODO cardano n peers?
