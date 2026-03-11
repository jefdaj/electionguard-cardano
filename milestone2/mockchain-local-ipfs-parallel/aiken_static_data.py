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
    json_strs.sort()
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
  metadata: er.{m}
}}""")

def manifest(n, j, c, s):
    m = 'Manifest'
    record(n, c, s, m)

def ceremony_details(n, j, c, s):
    m = 'CeremonyDetails'
    record(n, c, s, m)

def guardian_pubkey(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = f'GuardianPubkey {{ guardian_number: {i} }}'
    n = f'guardian{i}_pubkey'
    record(n, c, s, m)

def guardian_backup(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = f'GuardianBackup {{ guardian_number: {i}, backup_order: {b} }}'
    n = f'guardian{i}_backup{b}'
    record(n, c, s, m)

def guardian_verification(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = f'GuardianVerification {{ guardian_number: {i}, backup_order: {b} }}'
    n = f'guardian{i}_verification{b}'
    record(n, c, s, m)

def joint_key(n, j, c, s):
    m = 'JointKey'
    record(n, c, s, m)

def constants(n, j, c, s):
    m = 'Constants'
    record(n, c, s, m)

def device(n, j, c, s):
    i = int(j["device_number"])
    m = f'Device {{ device_number: {i} }}'
    record(n, c, s, m)

def ballot_submitted(n, j, c, s):
    i = f'string.to_bytearray(@"{j["ballot_id"]}")'
    m = f'Device {{ ballot_id: {i} }}'
    record(n, c, s, m)

render_fns = [
    # manifest,
    # ceremony_details,
    # guardian_pubkey,
    # guardian_backup,
    # guardian_verification,
    # joint_key,
    # constants,
    # TODO context?
    # device,
    ballot_submitted
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
        # print(json.dumps(j, indent=2))
        # print(j["record_type"])
