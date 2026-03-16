#!/usr/bin/env python3

# Usage:
# nix develop .#offchain
# ./static_records_py.py > static_election_records_py_out.py

from election.plutus import types
from multiformats_cid import cid, make_cid
from pathlib import Path
import json
import re
from pprint import pprint

IN_DIR = 'static_election_records'
IN_LOG = Path(IN_DIR) / 'egsync.log'

print('''# Generated with static_records_py.py. Consider editing and re-running that to make any changes.

from election.plutus.types import *
''')

#####################
# phases
#####################

PHASES = {
    0: types.ElectionConfigPhase(phase=types.ConfigAnnouncePhase()),
    1: types.ElectionConfigPhase(phase=types.ConfigOnboardingPhase()),
    2: types.ElectionConfigPhase(phase=types.ConfigCeremonyPhase()),
    3: types.ElectionVotingPhase(),
    4: types.ElectionResultsPhase(phase=types.ResultsTallyPhase()),
    5: types.ElectionResultsPhase(phase=types.ResultsDecryptPhase()),
    6: types.ElectionVerifyPhase(),
    7: types.ElectionFinalizePhase(),
}

print('STATIC_PHASES = \\')
pprint(PHASES, width=250)
print()

#####################
# transactions
#####################

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
    return (1, r)

def ceremony_details(n, j, s):
    m = types.CeremonyDetails()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def guardian_pubkey(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = types.GuardianPubkey(i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def guardian_backup(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = types.GuardianBackup(guardian_number=i, backup_order=b)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (2, r)

def guardian_verification(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = types.GuardianVerification(guardian_number=i, backup_order=b)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def summary(n, j, s):
    i = j["verifier_id"].replace('_', '') # TODO leave underscore?
    m = types.Summary(verifier_id=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    seqs = {
        'admin': 7,
        'guardian': 5,
        'verifier': 1,
    }
    for role in seqs.keys():
        if role in i:
            s = seqs[role]
    return (s, r)

def tally_share(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = types.TallyShare(guardian_number=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (4, r)

def spoiled_share(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    i2 = j["spoiled_id"]
    m = types.SpoiledShare(guardian_number=i, spoiled_id=i2)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (4, r)

def joint_key(n, j, s):
    m = types.JointKey()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def constants(n, j, s):
    m = types.Constants()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def ciphertext_tally(n, j, s):
    m = types.CiphertextTally()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (5, r)

def plaintext_tally(n, j, s):
    m = types.PlaintextTally()
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (6, r)

def device(n, j, s):
    i = int(j["device_number"])
    m = types.Device(device_number=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def ballot_name(prefix, j, key='ballot_id'):
    i = j[key]
    n = '_'.join(i.replace('ballot', prefix).split('-')[:2])
    return n

def ballot_submitted(n, j, s):
    i = j["ballot_id"]
    m = types.BallotSubmitted(ballot_id=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (2, r)

def spoiled_result(n, j, s):
    i = j["ballot_id"]
    m = types.SpoiledResult(ballot_id=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (6, r)

def ballot_spoiled(n, j, s):
    i = j["ballot_id"]
    m = types.BallotSpoiled(ballot_id=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def cast_notice(n, j, s):
    i = j["ballot_id"]
    m = types.CastNotice(ballot_id=i)
    r = types.PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

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

SUBCHANNELS = [
  types.ChannelIdHelper().from_string(i)
  for i in ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']
]

# TODO how to add info for when the admin advances phase?

# block: role: (ElectionAction, List[PublicRecord])
TXS = {
        'admin': {0: (types.InitElection(), []),
                  2: (types.AddSubChannels(channels=SUBCHANNELS)),
                  4: (types.AdvancePhase(), []), # TODO handle other advances!
                  8: (types.RmSubChannels(channels=SUBCHANNELS)),
                  9: (types.EndElection(), [])
                  }
}

for fn in render_fns:
    for j in JSONS:
        channel = j["mockchain_channel"]
        if channel == 'admin_1':
            channel = 'admin'
        # print(channel)
        cid_str = j["cid"]
        fn_name = fn.__name__
        if j["record_type"] == fn.__name__:
            # print(json.dumps(j, indent=2))
            (seq, records) = fn(fn_name, j, cid_str)
            item = (types.PostPublicRecords(), records)
            if not channel in TXS:
                TXS[channel] = {}
            if not seq in TXS[channel]:
                TXS[channel][seq] = []
            TXS[channel][seq].append(item)
        # print(j["record_type"])

print('STATIC_TRANSACTIONS = \\')
pprint(TXS, width=250)
