from fastapi import APIRouter
from . import config, node, election, wallet, phase, collateral, channel, ceremony, records, manifest, ipfs

router = APIRouter(prefix="/api")
router.include_router(config.router)
router.include_router(node.router)
router.include_router(ipfs.router)
router.include_router(election.router)
router.include_router(wallet.router)
router.include_router(phase.router)
router.include_router(collateral.router)
router.include_router(channel.router)
router.include_router(ceremony.router)
router.include_router(records.router)
router.include_router(manifest.router)
