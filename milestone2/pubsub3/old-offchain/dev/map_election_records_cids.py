#!/usr/bin/env python3

# Example usage:
#
# $ docker run --name ipfs -p 4001:4001 -p 5001:5001 -p 8080:8080 ipfs/kubo:v0.34.1
# $ nix develop .#offchain
# $ ./dev/map_election_records_cids.py
# then manually remove the final dir hash from the json

from pathlib import Path
import asyncio
import json
import aioipfs
import os

DATA_DIR = Path(__file__).parent.parent / "tests" / "data" / "election_records_flat"
OUT_FILE = Path(__file__).parent.parent / "tests" / "data" / "election_records_flat_cids.json"

print(DATA_DIR); print('exists? ', os.path.exists(DATA_DIR))
print(OUT_FILE)

async def map_election_records_cids():
    mapping = {}

    async with aioipfs.AsyncIPFS(
        host='127.0.0.1',
        port=5001,
    ) as client:

        try:
            async for entry in client.add(
                str(DATA_DIR),
                recursive=True,
                only_hash=True,
                cid_version=1,
            ):
                path = Path(entry["Name"])
                if path.is_dir():
                    continue
                rel = path.stem
                mapping[str(rel)] = entry["Hash"]  # path -> cid

        except aioipfs.exceptions.APIError as e:
            print("CODE:", e.code)
            print("MESSAGE:", e.message)
            print("RAW:", e.raw)
            raise  # or handle

    mapping = dict(sorted(mapping.items()))
    OUT_FILE.write_text(json.dumps(mapping, indent=2), encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(map_election_records_cids())
