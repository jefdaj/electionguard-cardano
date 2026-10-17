# ipfs-cluster testing

Usage:

```bash
nix develop

docker compose up -d

for n in {1..1000}; do
  # ballots are ~1M including the zk proofs?
  dd if=/dev/random of=test${n}.data bs=1M count=1
  ipfs-cluster-ctl add test${n}.data
  rm test${n}.data
done

# check that all 1000 files show up
ipfs-cluster-ctl pin ls | wc -l

# check that the data replicated to each node
for d in data/ipfs*; do du -h $d | tail -n1; done

docker compose down
sudo rm -rf data/
```
