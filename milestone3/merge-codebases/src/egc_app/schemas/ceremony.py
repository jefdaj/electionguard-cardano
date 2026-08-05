from pydantic import BaseModel

# TODO unify with CeremonyDetails
# TODO field and post validators?
class CeremonyCreate(BaseModel):
    number_of_guardians: int
    quorum: int
