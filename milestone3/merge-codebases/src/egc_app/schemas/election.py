from pydantic import BaseModel
from egc import ElectionConfig

class ElectionSubscribe(BaseModel):
    config: ElectionConfig
