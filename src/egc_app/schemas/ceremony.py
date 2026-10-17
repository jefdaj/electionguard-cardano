from pydantic import BaseModel

# TODO unify with egc.CeremonyDetails
# TODO field and post validators?
class CeremonyDetails(BaseModel):
    number_of_guardians: int
    quorum: int
