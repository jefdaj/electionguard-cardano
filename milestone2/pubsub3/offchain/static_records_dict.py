#!/usr/bin/env python3

# Usage:
# nix develop .#offchain
# ./static_records_dict.py > static_election_records_dict_out.py

from election.plutus import types
from multiformats_cid import cid, make_cid
from pathlib import Path
import json
import re
from pprint import pprint

IN_DIR = 'static_election_records'
IN_LOG = Path(IN_DIR) / 'egsync.log'

print('''# Generated with static_records_dict.py
# Consider editing and re-running that to make changes.

from election.plutus.types import *

STATIC_RECORDS = \\''')

VARS = {}

with open(IN_LOG, 'r') as f:
    lines = f.readlines()
    lines.sort()
    lines = [l for l in lines if 'fetch_public_record' in l]
    json_strs = [l[l.find('{'):-1].replace("'", '"') for l in lines]
    # json_strs.sort()
    JSONS = [json.loads(j) for j in json_strs]

def manifest(n, j, s):
    m = types.Manifest()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return r

def ceremony_details(n, j, s):
    m = types.CeremonyDetails()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return r

def guardian_pubkey(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = types.GuardianPubkey(i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return r

def guardian_backup(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = types.GuardianBackup(guardian_number=i, backup_order=b)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return r

def guardian_verification(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = types.GuardianVerification(guardian_number=i, backup_order=b)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def summary(n, j, s):
    i = j["verifier_id"].replace('_', '') # TODO leave underscore?
    m = types.Summary(verifier_id=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def tally_share(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = types.TallyShare(guardian_number=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def spoiled_share(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    i2 = j["spoiled_id"]
    m = types.SpoiledShare(guardian_number=i, spoiled_id=i2)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def joint_key(n, j, s):
    m = types.JointKey()
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def constants(n, j, s):
    m = types.Constants()
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def ciphertext_tally(n, j, s):
    m = types.CiphertextTally()
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def plaintext_tally(n, j, s):
    m = types.PlaintextTally()
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def device(n, j, s):
    i = int(j["device_number"])
    m = types.Device(device_number=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def ballot_name(prefix, j, key='ballot_id'):
    i = j[key]
    n = '_'.join(i.replace('ballot', prefix).split('-')[:2])
    return n

def ballot_submitted(n, j, s):
    i = j["ballot_id"]
    m = types.BallotSubmitted(ballot_id=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def spoiled_result(n, j, s):
    i = j["ballot_id"]
    m = types.SpoiledResult(ballot_id=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def ballot_spoiled(n, j, s):
    i = j["ballot_id"]
    m = types.BallotSpoiled(ballot_id=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

def cast_notice(n, j, s):
    i = j["ballot_id"]
    m = types.CastNotice(ballot_id=i)
    return types.PublicRecord(ipfs_cid=s, metadata=m)

render_fns = [
    manifest,
    ceremony_details,
    guardian_pubkey,
    guardian_backup,
    guardian_verification,
    joint_key,
    constants,
    # TODO context?
    device,
    ballot_submitted,
    ballot_spoiled,
    cast_notice,
    ciphertext_tally,
    tally_share,
    spoiled_share,
    plaintext_tally,
    spoiled_result,
    summary,
]

ITEMS = []

for fn in render_fns:
    for j in JSONS:
        cid_str = j["cid"]
        fn_name = fn.__name__
        if j["record_type"] == fn.__name__:
            # print(json.dumps(j, indent=2))
            item = fn(fn_name, j, cid_str)
            ITEMS.append(item)
        # print(j["record_type"])

pprint(ITEMS, width=200)
