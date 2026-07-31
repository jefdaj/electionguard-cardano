from fastapi import APIRouter
from . import config, node, election, wallet, phase, collateral

router = APIRouter(prefix="/api")
router.include_router(config.router)
router.include_router(node.router)
router.include_router(election.router)
router.include_router(wallet.router)
router.include_router(phase.router)
router.include_router(collateral.router)
