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
    s = str(b16)[3:-1]
    a = f'#"{s}"'
    return a

def record(n, c, s, m):
    print(f"""
const {n} = er.PublicRecord {{
  {c}
  cid: {s},
  metadata: r.{m}
}}""")

def manifest(n, j, c, s):
    # print(j)
    m = 'Manifest'
    record(n, c, s, m)

def ceremony_details(n, j, c, s):
    m = 'CeremonyDetails'
    record(n, c, s, m)

def guardian_pubkey(n, j, c, s):
    print(j)
    i = int(j["guardian_id"].split('_')[-1])
    m = f'GuardianPubkey {{ guardian_number: {i} }}'
    n = f'guardian{i}_pubkey'
    record(n, c, s, m)

render_fns = [
    manifest,
    ceremony_details,
    guardian_pubkey,
    # guardian_backup
    # guardian_verification
    # joint_key
    # constants
    # context
    # device
    # ballot_submitted
    # ballot_spoiled
    # cast_notice
    # ciphertext_tally
    # tally_share
    # spoiled_share
    # plaintext_tally
    # spoiled_result
    # summary
]

for j in JSONS:
    for fn in render_fns:
        comment = f'// orig base32: {j["cid"]}'
        cid_str = convert_cid_for_aiken(j["cid"])
        fn_name = fn.__name__
        if j["record_type"] == fn.__name__:
            fn(fn_name, j, comment, cid_str)
            continue
        # print(json.dumps(j, indent=2))
        # print(j["record_type"])
