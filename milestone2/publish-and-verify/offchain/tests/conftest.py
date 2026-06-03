import pytest

pytest_plugins = [
    "fixtures.ogmios",
    "fixtures.assets",
    "fixtures.wallet",
    "fixtures.script",
    "fixtures.funder",
    "fixtures.admin",
    "fixtures.election",
]

# import json
# from os.path import realpath, join, exists
# from pathlib import Path
# from pycardano import OgmiosV6ChainContext, Address, SigningKey, VerificationKeyHash, UTxO, MultiAsset
# from typing import Dict, List

# from election import wallet as ew
# from election import plutus as ep
# from election.plutus import script as eps
# from election.plutus.types.channel_id import *
# from election.roles import funder as erf
