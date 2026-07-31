from pydantic import BaseModel
from typing import Optional

class CollateralReturn(BaseModel):
    return_addr: Optional[str] = None
