#!/usr/bin/env python3

# This is the main orchestration script. For now it will expect to run from
# /repo inside the electionguard-python-makefile-docker-env container.

import subprocess
import json

from os import makedirs
from os.path import join
from pprint import pprint
from dotmap import DotMap


# NOTE see logs.py for electionguard's separate LOG
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s\n%(message)s\n')
LOG = logging.getLogger('electionguard-cardano')


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
            pprint(json.loads(stdout))
        if stderr is not None:
            stderr = stderr.strip()
            if len(stderr) > 0:
                print(stderr)
    except json.decoder.JSONDecodeError:
        msg = stdout
        if stderr is not None:
            msg += '\n' + stderr
        LOG.error(msg)


def build_manifest(cfg):
    # uncomment for interactive script:
    # question = input('Referendum-style question to be asked: ')
    question = 'Are pineapples still cool?'
    run_python_script([
        join(cfg.dirs.scripts, 'admin.py'), "build-manifest",
        "--public-records-dir", cfg.dirs.public,
        "--referendum-question", question,
    ])


def announce_key_ceremony(cfg):
    run_python_script([
        join(cfg.dirs.scripts, 'admin.py'), "announce-key-ceremony",
        "--guardian-count"    , str(cfg.guardians.count),
         "--quorum"           , str(cfg.quardians.quorum),
        "--public-records-dir", cfg.dirs.public,
    ])


def key_ceremony_round(cfg, current_round):
    for guardian_id, sequence_order in zip(cfg.guardians.ids, cfg.guardians.sequence_order):
        run_python_script([
            join(cfg.dirs.scripts, 'guardian.py'), "key-ceremony",
            "--guardian-count"         , str(cfg.guardians.count),
            "--quorum"                 , str(cfg.quardians.quorum),
            "--public-records-dir"     , cfg.dirs.public,
            "--private-records-dir"    , cfg.dirs.private,
            "--guardian-id"            , guardian_id,
            "--guardian-sequence-order", str(sequence_order),
            "--current-round"          , str(current_round),
        ])


def publish_joint_key(cfg):
    run_python_script([
        join(cfg.dirs.scripts, 'admin.py'), "publish-joint-key",
        "--public-records-dir", cfg.dirs.public,
    ])


def build_election(cfg):
    run_python_script([
        join(cfg.dirs.scripts, 'admin.py'), "build-election",
        "--guardian-count"    , str(cfg.guardians.count),
         "--quorum"           , str(cfg.quardians.quorum),
        "--public-records-dir", cfg.dirs.public,
    ])


def add_device(cfg):
    run_python_script([
        join(cfg.dirs.scripts, 'device.py'), "add-device",
        "--public-records-dir", cfg.dirs.public,
    ])


def vote(cfg, candidate_id, spoil=False):
    run_python_script([
        join(cfg.dirs.scripts, 'device.py'), "vote",
        "--guardian-count"     , str(cfg.guardians.count),
        "--quorum"             , str(cfg.quardians.quorum),
        "--public-records-dir" , cfg.dirs.public,
        "--private-records-dir", cfg.dirs.private,
        "--candidate-id"       , candidate_id,
        "--spoil"              , str(spoil),
    ])


def tally(cfg):
    run_python_script([
        join(cfg.dirs.scripts, 'admin.py'), "tally",
        "--guardian-count"     , str(cfg.guardians.count),
        "--quorum"             , str(cfg.quardians.quorum),
        "--public-records-dir" , cfg.dirs.public,
    ])


def decrypt_shares(cfg):
    for guardian_id, sequence_order in zip(cfg.guardians.ids, cfg.guardians.sequence_order):
        run_python_script([
            join(cfg.dirs.scripts, 'guardian.py'), "decrypt-share",
            "--guardian-count"         , str(cfg.guardians.count),
            "--quorum"                 , str(cfg.quardians.quorum),
            "--public-records-dir"     , cfg.dirs.public,
            "--private-records-dir"    , cfg.dirs.private,
            "--guardian-id"            , guardian_id,
            "--guardian-sequence-order", str(sequence_order),
        ])


def parse_config(cfg_path):
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
    cfg.guardians.sequence_order = [*range(1, cfg.guardians.count + 1)]
    cfg.guardians.ids = [f"guardian_{i}" for i in cfg.guardians.sequence_order]
    return cfg


def main(cfg):
    build_manifest(cfg)
    announce_key_ceremony(cfg)
    key_ceremony_round(cfg, 1)
    key_ceremony_round(cfg, 2)
    key_ceremony_round(cfg, 3)
    # TODO should there be a "publish final guardian records" step here?
    publish_joint_key(cfg)
    build_election(cfg)
    add_device(cfg)
    vote(cfg, candidate_id="referendum-question-affirmative-selection")
    vote(cfg, candidate_id="referendum-question-negative-selection")
    vote(cfg, candidate_id="referendum-question-affirmative-selection")
    vote(cfg, candidate_id="referendum-question-affirmative-selection", spoil=True)
    vote(cfg, candidate_id="referendum-question-negative-selection"   , spoil=True)
    tally(cfg)
    # decrypt_shares(cfg)
    # decrypt_combine()


if __name__ == '__main__':
    cfg = parse_config('multicontainer.json')
    main(cfg)
