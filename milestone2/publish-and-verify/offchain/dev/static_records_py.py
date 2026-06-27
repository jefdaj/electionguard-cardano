#!/usr/bin/env python3

# Usage:
# nix develop .#offchain
# ./dev/static_records_py.py > tests/data/static_records/generated.py

# TODO more standard logging?
# TODO fix underscores in node names

from pycardano import *
import sys
import os
from multiformats_cid import cid, make_cid
from pathlib import Path
import json
import re
from pprint import pprint


# Add the parent directory to sys.path so we can import egc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from egc import *

IN_DIR = os.path.join(os.path.dirname(__file__), '../tests/data/static_records/files')
IN_LOG = Path(IN_DIR) / 'egsync.log'

print('''# Generated with static_records_py.py. Consider editing and re-running that to make any changes.

from egc import *
''')

#####################
# phases
#####################

PHASES = {
    0: ElectionConfigPhase(phase=ConfigAnnouncePhase()),
    1: ElectionConfigPhase(phase=ConfigOnboardingPhase()),
    2: ElectionConfigPhase(phase=ConfigCeremonyPhase()),
    3: ElectionVotingPhase(),
    4: ElectionResultsPhase(phase=ResultsTallyPhase()),
    5: ElectionResultsPhase(phase=ResultsDecryptPhase()),
    6: ElectionVerifyPhase(),
    7: ElectionFinalizePhase(),
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
    m = Manifest()
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def ceremony_details(n, j, s):
    m = CeremonyDetails()
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def guardian_pubkey(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    m = GuardianPubkey(i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def guardian_backup(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = GuardianBackup(guardian_number=i, backup_order=b)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (2, r)

def guardian_verification(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    b = int(j["backup_order"])
    m = GuardianVerification(guardian_number=i, backup_order=b)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def summary(n, j, s):
    i = j["verifier_id"].replace('_', '').replace('admin1', 'admin')
    m = Summary(verifier_id=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
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
    m = TallyShare(guardian_number=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (4, r)

def spoiled_share(n, j, s):
    i = int(j["guardian_id"].split('_')[-1])
    i2 = j["spoiled_id"]
    m = SpoiledShare(guardian_number=i, spoiled_id=i2)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (4, r)

def joint_key(n, j, s):
    m = JointKey()
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def constants(n, j, s):
    m = Constants()
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def ciphertext_tally(n, j, s):
    m = CiphertextTally()
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (5, r)

def plaintext_tally(n, j, s):
    m = PlaintextTally()
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (6, r)

def device(n, j, s):
    i = int(j["device_number"])
    m = Device(device_number=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (1, r)

def ballot_name(prefix, j, key='ballot_id'):
    i = j[key]
    n = '_'.join(i.replace('ballot', prefix).split('-')[:2])
    return n

def ballot_submitted(n, j, s):
    i = j["ballot_id"]
    m = BallotSubmitted(ballot_id=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (2, r)

def spoiled_result(n, j, s):
    i = j["ballot_id"]
    m = SpoiledResult(ballot_id=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (6, r)

def ballot_spoiled(n, j, s):
    i = j["ballot_id"]
    m = BallotSpoiled(ballot_id=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

def cast_notice(n, j, s):
    i = j["ballot_id"]
    m = CastNotice(ballot_id=i)
    r = PublicRecord(ipfs_cid=s, metadata=m)
    return (3, r)

render_fns = [
    manifest,
    ceremony_details,
    guardian_pubkey,
    guardian_backup,
    guardian_verification,
    joint_key,
    constants,
    # TODO context? YES
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

# SUBCHANNELS = [
#   ChannelIdHelper().from_string(i)
#   for i in ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']
# ]
SUBCHANNELS = ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']

# TODO how to add info for when the admin advances phase?

# role: block: (ElectionAction, List[PublicRecord])
TXS = {
        'admin': {0: (InitElection()                      , []),
                  2: (AddSubChannels(channels=SUBCHANNELS), []),
                  4: (AdvancePhase()                      , []), # TODO handle other advances!
                  8: (RmSubChannels(channels=SUBCHANNELS) , []),
                  9: (EndElection()                       , [])
                  }
}

# pprint(JSONS)

for fn in render_fns:
    for j in JSONS:
        ppr = PostPublicRecords()
        channel = j["mockchain_channel"]
        channel = channel.replace('_', '')
        if channel == 'admin1':
            channel = 'admin'
        cid_str = j["cid"]
        fn_name = fn.__name__
        if j["record_type"] == fn_name:
            # print(json.dumps(j, indent=2))
            (seq, record) = fn(fn_name, j, cid_str)

            # TODO fix plutus data types, then hopefully this will clear itself up:

            # print('record dict:', record.__dict__)

            # print(f'record: {record}')
            # print(f'record type: {type(record)}')
            # print(f'channel: {channel}')
            # print(f'channel type: {type(channel)}')

            if not channel in TXS:
                TXS[channel] = {}
                # print(f'init {channel}')

            if not seq in TXS[channel]:
                TXS[channel][seq] = (ppr, [])
                # print(f'init {channel} seq {seq}')

            TXS[channel][seq][1].append(str(record))
            # pprint(TXS, width=250)

# This, along with str(record) above, is a hack to get rid of quotes around
# PublicRecord strings:
formatted = pformat(TXS, width=220).replace('"PublicRecord',
                                            'PublicRecord').replace('))"',
                                                                    '))')
print(f'STATIC_TRANSACTIONS = \\\n{formatted}')
