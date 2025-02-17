#!/usr/bin/env python3

# This is the main orchestration script. For now it will expect to run from
# /repo inside the electionguard-python-makefile-docker-env container.

import subprocess
import json

from os import makedirs
from os.path import join
from pprint import pprint
from pygments import highlight, lexers, formatters
from electionguard.logs import log_info


# NOTE see logs.py for electionguard's separate LOG
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s\n%(message)s\n')
LOG = logging.getLogger('electionguard-cardano')


MSKC_NUMBER_OF_GUARDIANS = 3
MSKC_QUORUM = 2
MSKC_ROOT = '/repo/multiscript_election'
MSKC_SRC = MSKC_ROOT

GUARDIAN_SEQUENCE_ORDERS = [*range(1, MSKC_NUMBER_OF_GUARDIANS + 1)]
GUARDIAN_IDS = [f"guardian_{i}" for i in GUARDIAN_SEQUENCE_ORDERS]

PUBLIC_RECORDS_DIR  = join(MSKC_ROOT, 'public_record')
PRIVATE_RECORDS_DIR = join(MSKC_ROOT, 'private_records')


def print_colorful_json(msg):
	# based on https://stackoverflow.com/a/32166163
	msg = msg.replace("'", '"')
	formatted_json = json.dumps(json.loads(msg), indent=2)
	colorful_json = highlight(
		formatted_json,
		lexers.JsonLexer(),
		formatters.TerminalFormatter()
	)
	print(colorful_json)

def run_python_script(args, **kwargs):
    # TODO docker exec inside each container here?
    args = ["poetry", "run"] + args
    kwargs.update(stdout=subprocess.PIPE, text=True)
    LOG.info(' '.join(args))
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    # expects scripts to print a json dump of some info
    # for example: print(json.dumps(locals()))
    # TODO not useful long term?
    try:
        stdout = stdout.strip()
        if len(stdout) > 0:
            print_colorful_json(stdout)
        if stderr is not None:
            stderr = stderr.strip()
            if len(stderr) > 0:
                print(stderr)
    except json.decoder.JSONDecodeError:
        msg = stdout
        if stderr is not None:
            msg += '\n' + stderr
        LOG.error(msg)


def build_manifest():
    # uncomment for interactive script:
    # question = input('Referendum-style question to be asked: ')
    question = 'Are pineapples still cool?'
    run_python_script([
        join(MSKC_SRC, 'admin.py'), "build-manifest",
        "--public-records-dir", PUBLIC_RECORDS_DIR,
        "--referendum-question", question,
    ])


def announce_key_ceremony():
    run_python_script([
        join(MSKC_SRC, 'admin.py'), "announce-key-ceremony",
        "--guardian-count"    , str(MSKC_NUMBER_OF_GUARDIANS),
         "--quorum"           , str(MSKC_QUORUM),
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


def publish_joint_key():
    run_python_script([
        join(MSKC_SRC, 'admin.py'), "publish-joint-key",
        "--public-records-dir", PUBLIC_RECORDS_DIR,
    ])


def build_election():
    run_python_script([
        join(MSKC_SRC, 'admin.py'), "build-election",
        "--guardian-count"    , str(MSKC_NUMBER_OF_GUARDIANS),
         "--quorum"           , str(MSKC_QUORUM),
        "--public-records-dir", PUBLIC_RECORDS_DIR,
    ])


def add_device():
    run_python_script([
        join(MSKC_SRC, 'device.py'), "add-device",
        "--public-records-dir", PUBLIC_RECORDS_DIR,
    ])


def vote(candidate_id, spoil=False):
    run_python_script([
        join(MSKC_SRC, 'device.py'), "vote",
        "--guardian-count"    , str(MSKC_NUMBER_OF_GUARDIANS),
        "--quorum"            , str(MSKC_QUORUM),
        "--public-records-dir", PUBLIC_RECORDS_DIR,
        "--candidate-id"      , candidate_id,
        "--spoil"             , str(spoil),
    ])


if __name__ == '__main__':
    build_manifest()
    announce_key_ceremony()
    key_ceremony_round(1)
    key_ceremony_round(2)
    key_ceremony_round(3)
    # TODO should there be a "publish final guardian records" step here?
    publish_joint_key()
    build_election()
    add_device()
    vote(candidate_id="referendum-question-affirmative-selection")
    vote(candidate_id="referendum-question-negative-selection")
    vote(candidate_id="referendum-question-affirmative-selection")
