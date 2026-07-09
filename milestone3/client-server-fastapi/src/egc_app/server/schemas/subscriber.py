from pydantic import BaseModel
from egc import SubscriberConfig

class SubscriberOut(BaseModel):
    policy_id: str
