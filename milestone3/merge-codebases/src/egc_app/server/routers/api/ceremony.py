import asyncio
from fastapi import APIRouter, Depends, Response
from egc_app.server.state import get_state
from egc_app import schemas
from egc import save_record
from egc.core.plutus.types import record
from electionguard import key_ceremony as eg_ceremony

router = APIRouter(prefix="/ceremony")

@router.post("/create")
async def ceremony_create(data: schemas.CeremonyCreate, state=Depends(get_state)):
    # TODO reject if there's already a set of details? or should that update it?
    rtp_dir = state.node.records_to_post_dir
    obj = eg_ceremony.CeremonyDetails(
        number_of_guardians = data.number_of_guardians,
        quorum = data.quorum,
    )
    metadata = record.CeremonyDetails()
    save_record(metadata, obj, rtp_dir)
    return Response(status_code=201)
