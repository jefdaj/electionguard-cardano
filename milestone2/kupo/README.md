# Test kupo with a random token from CardanoScan

Usage:

Start the cardano-node-ogmios docker compose first.
Then run this to scan for recent transactions involving a specific asset.

```bash
# picked arbitrarily from top CardanoScan tokens for testing
# TODO delete the db when changing it, or name db mount by hash
asset_policy_id=7c833f1eb9b70c2e700d028e0ee28d421edad2af4222061be525382d
export KUPO_MATCH_PREVIEW="${asset_policy_id}.*"

# --since {slot-no.header_hash}
# this is 2025-02-08 ~16:24 UTC
export KUPO_SINCE_PREVIEW=72375623.c51ae5ba507e80df946e150644c3c50a94ea49c10b091c7fe55b2d55e5088de4

docker compose up -d
```
