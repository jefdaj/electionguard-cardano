from fastapi import APIRouter
from egc_app.server.schemas.health import HealthOut

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthOut)
async def health():
    return HealthOut()
