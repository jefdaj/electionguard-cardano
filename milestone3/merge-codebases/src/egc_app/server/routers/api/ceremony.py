import asyncio
from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
from egc import save_record, load_record, CeremonyDetails
from egc.core.plutus.types import record
from electionguard import key_ceremony as eg_ceremony


import logging
LOG = logging.getLogger(__name__)


router = APIRouter(prefix="/ceremony")


@router.post("/create")
async def ceremony_create(data: schemas.CeremonyDetails, state=Depends(get_state)):
    # TODO reject if there's already a set of details? or should that update it?
    rtp_dir = state.node.records_to_post_dir
    obj = eg_ceremony.CeremonyDetails(
        number_of_guardians = data.number_of_guardians,
        quorum = data.quorum,
    )
    metadata = record.CeremonyDetails()
    save_record(metadata, obj, rtp_dir)
    return Response(status_code=201)


@router.get("")
async def ceremony_show(state=Depends(get_state)):
    rf_dir = state.node.records_fetched_dir
    rec = load_record(CeremonyDetails(), rf_dir)
    out = schemas.CeremonyDetails(
        number_of_guardians = rec.number_of_guardians,
        quorum = rec.quorum,
    )
    LOG.debug(f'ceremony_show out: {out}')
    return out
