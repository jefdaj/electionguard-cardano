#!/usr/bin/env python3

# references:
# https://aiken-lang.org/example--hello-world/end-to-end/pycardano
# https://ogmios-python.readthedocs.io/en/latest/examples/build_tx_pycardano.html

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
context = OgmiosV6ChainContext("172.13.0.3", 1337)
