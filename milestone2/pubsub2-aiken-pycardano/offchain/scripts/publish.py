# scripts/publish.py
#!/usr/bin/env python3

"""
Publish IPFS CIDs to a new channel.

Usage:
    python scripts/publish.py <cid1> <cid2> ...
"""

import sys
from pathlib import Path
from pycardano import OgmiosChainContext, Network
from pubsub.client import PubSubClient
from pubsub.utils.keys import load_signing_key
from pubsub.utils.ipfs import IPFSClient

def main():
    if len(sys.argv) < 2:
        print("Usage: publish.py <cid1> <cid2> ...")
        sys.exit(1)
    
    cids = sys.argv[1:]
    
    # Setup
    context = OgmiosChainContext(
        ws_url="ws://localhost:1337",
        network=Network.TESTNET
    )
    
    publisher_key = load_signing_key("keys/publisher.skey")
    
    client = PubSubClient(
        chain_context=context,
        validator_script_path="../onchain/plutus.json",
        ipfs_client=IPFSClient()
    )
    
    # Publish
    print(f"Publishing {len(cids)} CIDs...")
    tx_hash = client.publish_cids(publisher_key, cids)
    print(f"Transaction submitted: {tx_hash}")
    print(f"View on Preview: https://preview.cardanoscan.io/transaction/{tx_hash}")

if __name__ == "__main__":
    main()

