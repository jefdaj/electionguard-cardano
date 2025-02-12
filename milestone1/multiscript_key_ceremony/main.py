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

# ROUND 1
election_keypairs_dir = join(MSKC_ROOT, 'public_record')
guardian_keys_dir     = join(MSKC_ROOT, 'guardian_keys')
makedirs(guardian_keys_dir, exist_ok=True)
makedirs(election_keypairs_dir, exist_ok=True)
# print(election_keypairs_dir)
# print(guardian_keys_dir)

for guardian_id, sequence_order in zip(guardian_ids, guardian_sequence_orders):
    # print(guardian_id, sequence_order)
    # self._guardian_generates_keys(guardian_id, sequence_order)
    proc = subprocess.Popen([
        "poetry", "run", join(MSKC_SRC, 'guardian.py'), "key-ceremony",
        "--guardian-count"         , str(MSKC_NUMBER_OF_GUARDIANS),
        "--quorum"                 , str(MSKC_QUORUM),
        "--guardian-keys-dir"      , guardian_keys_dir,
        "--guardian-id"            , guardian_id,
        "--guardian-sequence-order", str(sequence_order),
        "--current-round"          , str(1),
    ], stdout=subprocess.PIPE, text=True)
    pprint(json.loads(proc.communicate()[0]))
    # break

# self.assertEqual(len(self.election_key_pairs), self.NUMBER_OF_GUARDIANS)
