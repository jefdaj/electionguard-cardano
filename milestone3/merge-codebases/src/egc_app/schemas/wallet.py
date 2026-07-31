from pydantic import BaseModel
from egc import Wallet

class WalletLoadOrCreate(BaseModel):
    wallet_or_desc: Wallet|str # if str, generate using description
