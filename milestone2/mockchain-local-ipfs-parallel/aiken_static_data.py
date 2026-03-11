#!/usr/bin/env python3

# Usage:
#
# nix develop
# sudo rm -r data
# ./election.sh
# sudo cp -r ./data/private/verifier_1/egsync ./aiken_static_data
# sudo chown $(whoami) ./aiken_static_data -R
# exit
#
# nix develop .#egsync
# ./aiken_static_data.py

from multiformats_cid import cid, make_cid
from pathlib import Path
import json

IN_DIR = 'aiken_static_data'
IN_LOG = Path(IN_DIR) / 'egsync.log'
OUT_AK = 'aiken_static_data.ak'

with open(IN_LOG, 'r') as f:
    lines = f.readlines()
    lines = [l for l in lines if 'fetch_public_record' in l]
    json_strs = [l[l.find('{'):-1].replace("'", '"') for l in lines]
    JSONS = [json.loads(j) for j in json_strs]

def convert_cid_for_aiken(cid_str):
    # print(f'cid_str: {cid_str}')
    c = make_cid(cid_str)
    # print(c)
    # print(c.version)
    b16 = c.encode('base16')
    s = str(b16)[2:-1]
    a = f'#"{s}"'
    return a

for j in JSONS:
    if j["record_type"] == "manifest":
        print(json.dumps(j, indent=2))
        print()
        print(f'// orig cid: {j["cid"]}')
        print(convert_cid_for_aiken(j["cid"]))
