from fastapi import APIRouter
from . import config, node, election, wallet, phase
from .election.router import router as election_router

router = APIRouter(prefix="/api")
router.include_router(config.router)
router.include_router(node.router)
router.include_router(election_router)
router.include_router(wallet.router)
router.include_router(phase.router)
