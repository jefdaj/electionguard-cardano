#!/usr/bin/env python3

import hashlib
import json
import logging
import os
import subprocess

from glob import glob
from hypothesis import given, settings, seed

from config import *
from election import main, init_log, parse_config


### given_election_testdir: supply cached arbitrary elections ###

TESTS_DIR = './tests'

def hash_config(cfg: ProjectConfig, truncate=99) -> str:
    "Ensures tmpdirs are not being reused after their configs change"
    s = str(cfg).encode('utf-8')
    d = hashlib.md5(s).digest()
    return d.hex()[:truncate]

ElectionTestDir = str

def run_test_election(cfg: ProjectConfig) -> ElectionTestDir:

    # use our own custom tmpdir instead of TemporaryDirectory
    h5 = hash_config(cfg, truncate=5)
    test_name = f'test{h5}'
    tmpdir = os.path.join(TESTS_DIR, test_name)

    # This should prevent more than one run_test_election from running with the
    # same config at the same time. Not sure whether that happens in practice,
    # but better to be safe than sorry when using pytest -n<threads>, right?
    # TODO why is it making only one election run at a time though?
    lockfile = os.path.join(tmpdir, 'election.lock')

    if os.path.exists(tmpdir):
        # if another instance is running, wait for it to finish
        while os.path.exists(lockfile):
            time.sleep(1)
        return

    try:
        os.makedirs(tmpdir)
        lock = open(lockfile, 'w')

        data_dir = os.path.join(tmpdir, cfg['arion']['data_dir'])
        logfile  = os.path.join(tmpdir, 'election.log')

        os.makedirs(data_dir, exist_ok=False) # TODO remove?

        # TODO leave data_dir as 'data' and resolve inside election.py?
        cfg['arion']['data_dir'] = data_dir
        cfg['arion']['project_name'] = test_name

        cfg_path = os.path.join(tmpdir, 'election.json') # TODO rename config?
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f)

        cfg = parse_config(cfg_path, pause_to_explain=False)
        log = init_log(cfg, logfile, logging.INFO)
        main(cfg, log)

    except:
        # TODO rm here? or do we want to keep + inspect the error files?
        # shutil.rmtree(tmpdir, ignore_errors=True)
        raise

    finally:
        lock.close()
        os.remove(lockfile)

    return tmpdir

# https://stackoverflow.com/a/4122845
def yad(decorators):
    def decorator(f):
        for d in reversed(decorators):
            f = d(f)
        return f
    return decorator

# Convert a test that takes a cfg to one which takes a pre-run election testdir
# generated from that cfg.
def prerun_election_cfg(fn_from_testdir):
    def fn_from_cfg(cfg: ProjectConfig, *args, **kwargs):
        testdir: ElectionTestDir = run_test_election(cfg)
        return fn_from_testdir(testdir, *args, **kwargs)
    return fn_from_cfg

def get_random_seed():
    # random seed can be set per dev session, which offers a good
    # balance between caching and making sure different values work
    try:
        random_seed: int = int(os.environ['TEST_RANDOM_SEED'])
    except KeyError:
        random_seed = 1234
    return random_seed

# A somewhat mind bending hack to make hypothesis reuse cached test elections.
# This way we can define a lot of rapid tests that make individual assertions
# about the results. It's kind of like a hybrid between givens and pytest
# fixtures: we generate the election configs randomly, but then reuse the same
# random values across lots of tests.
#
# Notes:
# - prerun_election_cfg is a separate idea that was also convenient to tack on here
# - max_examples really is a max; hypothesis will often run fewer
#
# TODO is this a partial solution to https://github.com/HypothesisWorks/hypothesis/issues/114
# TODO top level CLI arg for max_examples here?
# TODO if no args needed, remove this def lambda
def given_election_testdir():
    return yad([
        seed(get_random_seed()),
        settings(max_examples=3, deadline=None),
        given(cfg=projectconfig()),
        prerun_election_cfg,
    ])


### misc small test helpers ###

def load_json(json_path: str):
    with open(json_path, 'r') as f:
        return json.load(f)

# TODO is the return type right?
def load_election_config_json(testdir: str) -> ProjectConfig:
    json_path = join(testdir, 'election.json')
    return load_json(json_path)

def load_summary_json(testdir: str, verifier_id: str) -> dict:
    json_path = join(testdir, f'data/public/4_verify/{verifier_id}.json')
    return load_json(json_path)

def election_verified(testdir: str, verifier_id: str) -> bool:
    try:
        summary = load_summary_json(testdir, verifier_id)
        return summary['Verified']
    except:
        return False


### property tests ###

@given_election_testdir()
def test_election_verified_by_admin(testdir: ElectionTestDir):
    assert election_verified(testdir, 'admin1')

@given_election_testdir()
def test_all_election_verifiers_agree(testdir: ElectionTestDir):
    first_summary: Optional[dict] = None
    json_paths = glob(join(testdir, 'data/public/4_verify/*.json'))
    for json_path in json_paths:
        summary = load_json(json_path)
        if first_summary is None:
            first_summary = summary
        else:
            assert summary == first_summary

@given_election_testdir()
def test_n_verifications(testdir: ElectionTestDir):
    config = load_election_config_json(testdir)
    n_expected = sum([
        1, # admin
        config['election']['guardians']['count'],
        config['election']['verifiers']['count'],
    ])
    n_actual = len(glob(join(testdir, 'data/public/4_verify/*.json')))
    assert n_actual == n_expected

@given_election_testdir()
def test_election_property_3(testdir: ElectionTestDir):
    assert True
    # TODO write this

@given_election_testdir()
def test_election_property_4(testdir: ElectionTestDir):
    assert True
    # TODO write this

@given_election_testdir()
def test_election_property_5(testdir: ElectionTestDir):
    assert True
    # TODO write this


### main ###

if __name__ == '__main__':
   args = ['pytest', 'test.py', '-vv']
   subprocess.check_call(args)
