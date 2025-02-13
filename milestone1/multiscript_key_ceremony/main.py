#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test. Instead of one
# script, this has one script per party and they coordinate via a shared folder
# on the local filesystem.
#
# In this first version, I'll just have the main script call the others
# repeatedly and tell them which phase/round of the protocol to run each time.
# Later they should all be running at the same time and figuring it out
# themselves as files are added to the shared folder.
#
# This is the main orchestration script. For now it will expect to run from
# /repo inside the electionguard-python-makefile-docker-env container.

import subprocess
import json

from os import makedirs
from os.path import join
from pprint import pprint

MSKC_NUMBER_OF_GUARDIANS = 5
MSKC_QUORUM = 3
MSKC_ROOT = '/repo/multiscript_key_ceremony'
MSKC_SRC = MSKC_ROOT

# TODO admin setup first?

guardian_sequence_orders = [*range(1, MSKC_NUMBER_OF_GUARDIANS + 1)]
guardian_ids = [f"guardian_{i}" for i in guardian_sequence_orders]
# print(guardian_sequence_orders)
# print(guardian_ids)

### ROUND 1 ###

public_records_dir  = join(MSKC_ROOT, 'public_record')
private_records_dir = join(MSKC_ROOT, 'private_records')
makedirs(private_records_dir, exist_ok=True)
makedirs(public_records_dir, exist_ok=True)
# print(public_records_dir)
# print(private_records_dir)

for guardian_id, sequence_order in zip(guardian_ids, guardian_sequence_orders):
    # print(guardian_id, sequence_order)
    # self._guardian_generates_keys(guardian_id, sequence_order)
    proc = subprocess.Popen([
        # TODO docker exec inside each container here?
        "poetry", "run", join(MSKC_SRC, 'guardian.py'), "key-ceremony",
        "--guardian-count"         , str(MSKC_NUMBER_OF_GUARDIANS),
        "--quorum"                 , str(MSKC_QUORUM),
        "--public-records-dir"     , join(public_records_dir, 'guardians'),
        "--private-records-dir"    , join(private_records_dir, guardian_id),
        "--guardian-id"            , guardian_id,
        "--guardian-sequence-order", str(sequence_order),
        "--current-round"          , str(1),
    ], stdout=subprocess.PIPE, text=True)
    (stdout, stderr) = proc.communicate()
    try:
        pprint(json.loads(stdout))
    except json.decoder.JSONDecodeError:
        print(stdout)
        print(stderr)

### ROUND 2 ###

for guardian_id, sequence_order in zip(guardian_ids, guardian_sequence_orders):
    # print(guardian_id, sequence_order)
    # self._guardian_generates_keys(guardian_id, sequence_order)
    proc = subprocess.Popen([
        # TODO docker exec inside each container here?
        "poetry", "run", join(MSKC_SRC, 'guardian.py'), "key-ceremony",
        "--guardian-count"         , str(MSKC_NUMBER_OF_GUARDIANS),
        "--quorum"                 , str(MSKC_QUORUM),
        "--public-records-dir"     , join(public_records_dir, 'guardians'),
        "--private-records-dir"    , join(private_records_dir, guardian_id),
        "--guardian-id"            , guardian_id,
        "--guardian-sequence-order", str(sequence_order),
        "--current-round"          , str(2),
    ], stdout=subprocess.PIPE, text=True)
    (stdout, stderr) = proc.communicate()
    try:
        pprint(json.loads(stdout))
    except json.decoder.JSONDecodeError:
        print(stdout)
        print(stderr)
