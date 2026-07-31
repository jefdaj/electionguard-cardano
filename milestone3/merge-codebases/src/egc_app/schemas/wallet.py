from pydantic import BaseModel
from egc import Wallet

class WalletLoadOrCreate(BaseModel):
    # TODO SigningKey|str?
    wallet_or_desc: Wallet|str # if str, generate using description
