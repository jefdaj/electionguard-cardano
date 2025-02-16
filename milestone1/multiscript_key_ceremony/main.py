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


MSKC_NUMBER_OF_GUARDIANS = 3
MSKC_QUORUM = 2
MSKC_ROOT = '/repo/multiscript_key_ceremony'
MSKC_SRC = MSKC_ROOT

GUARDIAN_SEQUENCE_ORDERS = [*range(1, MSKC_NUMBER_OF_GUARDIANS + 1)]
GUARDIAN_IDS = [f"guardian_{i}" for i in GUARDIAN_SEQUENCE_ORDERS]

PUBLIC_RECORDS_DIR  = join(MSKC_ROOT, 'public_record')
PRIVATE_RECORDS_DIR = join(MSKC_ROOT, 'private_records')
makedirs(PRIVATE_RECORDS_DIR, exist_ok=True)
makedirs(PUBLIC_RECORDS_DIR, exist_ok=True)


def run_python_script(args):
    # TODO docker exec inside each container here?
    args = ["poetry", "run"] + args
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
    (stdout, stderr) = proc.communicate()
    try:
        pprint(json.loads(stdout))
    except json.decoder.JSONDecodeError:
        print(stdout)
        print(stderr)


def announce_key_ceremony():
    run_python_script([
        join(MSKC_SRC, 'admin.py'), "announce-key-ceremony",
        "--guardian-count"    , str(MSKC_NUMBER_OF_GUARDIANS),
         "--quorum"           , str(MSKC_QUORUM),
        "--public-records-dir", PUBLIC_RECORDS_DIR,
    ])


def publish_joint_key():
    run_python_script([
        join(MSKC_SRC, 'admin.py'), "publish-joint-key",
        "--public-records-dir", PUBLIC_RECORDS_DIR,
    ])


def key_ceremony_round(current_round):
    for guardian_id, sequence_order in zip(GUARDIAN_IDS, GUARDIAN_SEQUENCE_ORDERS):
        run_python_script([
            join(MSKC_SRC, 'guardian.py'), "key-ceremony",
            "--guardian-count"         , str(MSKC_NUMBER_OF_GUARDIANS),
            "--quorum"                 , str(MSKC_QUORUM),
            "--public-records-dir"     , PUBLIC_RECORDS_DIR,
            "--private-records-dir"    , PRIVATE_RECORDS_DIR,
            "--guardian-id"            , guardian_id,
            "--guardian-sequence-order", str(sequence_order),
            "--current-round"          , str(current_round),
        ])


if __name__ == '__main__':
    announce_key_ceremony()
    key_ceremony_round(1)
    key_ceremony_round(2)
    key_ceremony_round(3)
    # TODO should there be a "publish final guardian records" step here?
    publish_joint_key()
