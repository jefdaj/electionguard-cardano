from fastapi import APIRouter
from . import health, subscriber

router = APIRouter(prefix="/api")
router.include_router(health.router)
router.include_router(subscriber.router)
