#!/usr/bin/env python3

"""
Publish IPFS CIDs to a new channel.

Usage:
    python scripts/publish.py <cid1> <cid2> ...
"""

import sys

from pathlib import Path
from pycardano import OgmiosChainContext, Network

# from pubsub import IPFSClient
from pubsub import PubsubClient, load_test_wallet_signing_key

def main():
    # if len(sys.argv) < 2:
        # print("Usage: publish.py <cid1> <cid2> ...")
        # sys.exit(1)
    # cids = sys.argv[1:]

    ctx = OgmiosChainContext(
        ws_url="ws://localhost:1337", # TODO also http?
        network=Network.TESTNET
    )

    sk = load_test_wallet_signing_key()

    ps = PubsubClient(
        chain_context=ctx,
        plutus_json_path="../onchain/plutus.json",
        signing_key=sk
        # ipfs_client=IPFSClient()
    )

    return ps
    # TODO write the rest of this

    # Publish
    # print(f"Publishing {len(cids)} CIDs...")
    # # tx_hash = ps.publish_cids(publisher_key, cids)
    # print(f"Transaction submitted: {tx_hash}")
    # print(f"View on Preview: https://preview.cardanoscan.io/transaction/{tx_hash}")

if __name__ == "__main__":
    main()

