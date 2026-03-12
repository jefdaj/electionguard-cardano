#!/usr/bin/env python3

# Usage:
#
# cd ../mockchain-local-ipfs-parallel
# nix develop
# sudo rm -r data
# ./election.sh
# sudo cp -r ./data/private/verifier_1/egsync ./aiken_static_data
# sudo chown $(whoami) ./aiken_static_data -R
# exit
#
# nix develop .#egsync
# ../pubsub3/onchain/static_election_records.py > ../pubsub3/onchain/validators/tests/data/static_election_records.ak

from multiformats_cid import cid, make_cid
from pathlib import Path
import json
import re

IN_DIR = 'static_election_records'
IN_LOG = Path(IN_DIR) / 'egsync.log'

print('''// Generated with static_election_records.py
// Consider editing and re-running that to make changes.

use aiken/primitive/string.{to_bytearray}
use election/record as er''')

VARS = {}

with open(IN_LOG, 'r') as f:
    lines = f.readlines()
    lines.sort()
    lines = [l for l in lines if 'fetch_public_record' in l]
    json_strs = [l[l.find('{'):-1].replace("'", '"') for l in lines]
    # json_strs.sort()
    JSONS = [json.loads(j) for j in json_strs]

def convert_cid_for_aiken(cid_str):
    """Convert an IPFS CID string to Aiken ByteArray format."""
    c = make_cid(cid_str)

    # Get the raw bytes from the CID's buffer attribute
    cid_bytes = c.buffer

    # Convert to hex string
    hex_str = cid_bytes.hex()

    # Return in Aiken ByteArray format
    return f'#"{hex_str}"'

def record(n, c, s, m):
    print(f"""
pub const {n} = er.PublicRecord {{
  {c}
  cid: {s},
  metadata: er.{m}
}}""")
    return n

def manifest(n, j, c, s):
    m = 'Manifest'
    return record(n, c, s, m)

def ceremony_details(n, j, c, s):
    m = 'CeremonyDetails'
    return record(n, c, s, m)

def guardian_pubkey(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = f'GuardianPubkey {{ guardian_number: {i} }}'
    n = f'guardian{i}_pubkey'
    return record(n, c, s, m)

def summary(n, j, c, s):
    i = j["verifier_id"].replace('_', '') # TODO leave underscore?
    n = f'{i}_summary'
    i = f'to_bytearray(@"{i}")' # TODO remove?
    m = f'Summary {{ verifier_id: {i} }}'
    return record(n, c, s, m)

def tally_share(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = f'TallyShare {{ guardian_number: {i} }}'
    n = f'guardian{i}_tally_share'
    return record(n, c, s, m)

def spoiled_share(n, j, c, s):
    n = ballot_name('spoiled_share', j, 'spoiled_id')
    i = int(j["guardian_id"].split('_')[-1])
    n = f'guardian{i}_{n}'
    i2 = j["spoiled_id"]
    i2 = f'to_bytearray(@"{i2}")' # TODO remove?
    m = f'''SpoiledShare {{
    guardian_number: {i},
    spoiled_id: {i2},
  }}'''
    return record(n, c, s, m)

def guardian_backup(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = f'GuardianBackup {{ guardian_number: {i}, backup_order: {b} }}'
    n = f'guardian{i}_backup{b}'
    return record(n, c, s, m)

def guardian_verification(n, j, c, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = f'GuardianVerification {{ guardian_number: {i}, backup_order: {b} }}'
    n = f'guardian{i}_verification{b}'
    return record(n, c, s, m)

def joint_key(n, j, c, s):
    m = 'JointKey'
    return record(n, c, s, m)

def constants(n, j, c, s):
    m = 'Constants'
    return record(n, c, s, m)

def ciphertext_tally(n, j, c, s):
    m = 'CiphertextTally'
    return record(n, c, s, m)

def plaintext_tally(n, j, c, s):
    m = 'PlaintextTally'
    return record(n, c, s, m)

def device(n, j, c, s):
    i = int(j["device_number"])
    m = f'Device {{ device_number: {i} }}'
    n = f'device{i}'
    return record(n, c, s, m)

def ballot_name(prefix, j, key='ballot_id'):
    i = j[key]
    n = '_'.join(i.replace('ballot', prefix).split('-')[:2])
    return n

def ballot_submitted(n, j, c, s):
    i = j["ballot_id"]
    n = ballot_name('ballot_submitted', j)
    i = f'to_bytearray(@"{i}")'
    m = f'BallotSubmitted {{ ballot_id: {i} }}'
    return record(n, c, s, m)

def spoiled_result(n, j, c, s):
    i = j["ballot_id"]
    n = ballot_name('spoiled_result', j)
    i = f'to_bytearray(@"{i}")'
    m = f'SpoiledResult {{ ballot_id: {i} }}'
    return record(n, c, s, m)


def ballot_spoiled(n, j, c, s):
    i = j["ballot_id"]
    n = ballot_name('ballot_spoiled', j)
    i = f'to_bytearray(@"{i}")'
    m = f'BallotSpoiled {{ ballot_id: {i} }}'
    return record(n, c, s, m)

def cast_notice(n, j, c, s):
    i = j["ballot_id"]
    n = ballot_name('cast_notice', j)
    i = f'to_bytearray(@"{i}")'
    m = f'CastNotice {{ ballot_id: {i} }}'
    return record(n, c, s, m)

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

VARNAMES = []

# generate individual records
for fn in render_fns:
    for j in JSONS:
        comment = f'// orig base32: {j["cid"]}'
        cid_str = convert_cid_for_aiken(j["cid"])
        fn_name = fn.__name__
        if j["record_type"] == fn.__name__:
            varname = fn(fn_name, j, comment, cid_str)
            VARNAMES.append(varname)
        # print(json.dumps(j, indent=2))
        # print(j["record_type"])

# VARNAMES = sorted(VARNAMES)

# generate lists
lists = {
    'admin' : '(manifest|joint_key|constants|ceremony_details|ciphertext_tally|plaintext_tally|.*admin.*summary.*)',
    'guardian1' : 'guardian1',
    'guardian2' : 'guardian2',
    'guardian3' : 'guardian3',
    'ballot_submitted' : 'ballot_submitted',
    'ballot_spoiled' : 'ballot_spoiled',
    'cast_notice' : 'cast_notice',
    'spoiled_share' : '.*spoiled_share.*',
    'spoiled_result' : 'spoiled_result',
    'device1' : '(device|ballot_submitted|ballot_spoiled|cast_notice)',
    'verifier1' : 'verifier1',
    'summary' : '.*_summary',
    'all' : '.*',
}

for list_name, list_regex in lists.items():
    print(f'\npub const {list_name}_records = [')
    for v in VARNAMES:
        if re.match(list_regex, v):
            print(f'  {v},')
    print(']')
