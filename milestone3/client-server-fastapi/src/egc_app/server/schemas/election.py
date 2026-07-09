from pydantic import BaseModel
from egc import SubscriberConfig

class ElectionOut(BaseModel):
    sub_cfg: SubscriberConfig
