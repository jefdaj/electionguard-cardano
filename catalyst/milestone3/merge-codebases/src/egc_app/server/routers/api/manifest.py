import asyncio
from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
from egc import save_record, EgcManifest
from egc.core.plutus.types import record

import logging
LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/manifest")

@router.post("") # TODO /create?
async def manifest_create(data: dict, state=Depends(get_state)):
    LOG.info(f'data: {data}')
    egc_manifest = EgcManifest.from_dict(data)
    eg_manifest = egc_manifest.to_eg()
    LOG.info(f'eg_manifest: {eg_manifest}')
    # TODO reject if there's already a set of details? or should that update it?
    rtp_dir = state.node.records_to_post_dir
    metadata = record.Manifest()
    save_record(metadata, eg_manifest, rtp_dir)
    return Response(status_code=201)
