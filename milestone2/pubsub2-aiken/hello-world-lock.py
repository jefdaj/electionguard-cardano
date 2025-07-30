from pycardano import (
    # BlockFrostChainContext,
    OgmiosV6ChainContext,
)
import os

# context = BlockFrostChainContext(
#     project_id=os.environ["BLOCKFROST_PROJECT_ID"],
#     base_url="https://cardano-preview.blockfrost.io/api/",
# )

# TODO thread host and port from top level arion-compose
# TODO does it work now??
context = OgmiosV6ChainContext("172.13.0.3", 1337)
