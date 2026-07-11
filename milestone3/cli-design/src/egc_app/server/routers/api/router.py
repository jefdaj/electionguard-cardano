from fastapi import APIRouter
from . import config, status, election

router = APIRouter(prefix="/api")
router.include_router(config.router)
router.include_router(status.router)
router.include_router(election.router)
