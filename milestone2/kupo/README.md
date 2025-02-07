# Test kupo with a random token from CardanoScan

Usage:

```
./run-kupo.sh
# in another terminal:
nix-shell -p jq
curl 'http://localhost:1442/matches' | jq | head -n1000 | less
```
