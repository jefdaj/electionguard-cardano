from fastapi import APIRouter
from . import health, election

router = APIRouter(prefix="/api")
router.include_router(health.router)
router.include_router(election.router)
