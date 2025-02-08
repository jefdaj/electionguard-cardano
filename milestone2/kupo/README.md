# Test kupo with a random token from CardanoScan

Usage:

Start the cardano-node-ogmios docker compose first.
Then run this to scan for recent transactions involving a specific asset.

```bash
# picked arbitrarily from recent CardanoScan transactions
# TODO delete the db when changing it, or name db mount by hash
asset_policy_id=c450b3e21b1e98bb559bfbaf3b9fd9df60d7df9e0ce62cedd56912ea
export KUPO_MATCH_PREVIEW="${asset_policy_id}.*"

# --since {slot-no.header_hash}
# this is 2025-02-08 ~16:24 UTC
export KUPO_SINCE_PREVIEW=72375623.c51ae5ba507e80df946e150644c3c50a94ea49c10b091c7fe55b2d55e5088de4

docker compose up -d

nix-shell -p jq
curl 'http://localhost:1442/matches' | jq > matches.json
```

Verdict: works very well! Syncs immediately when starting `--since` the
current slot, which we can do for elections. Provides simple JSON of matches.
