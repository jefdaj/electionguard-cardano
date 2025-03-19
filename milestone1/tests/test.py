#!/usr/bin/env python3

import hashlib
import json
import logging
import os
# import shutil
import string
import subprocess
import tempfile
import time

from hypothesis import given, settings, seed

from config import *
from election import main, init_log, parse_config


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
        settings(max_examples=10, deadline=None),
        given(cfg=projectconfig()),
        prerun_election_cfg,
    ])


# TODO fill these out with useful properties

@given_election_testdir()
def test_election_property_1(testdir: ElectionTestDir):
    assert True

@given_election_testdir()
def test_election_property_2(testdir: ElectionTestDir):
    assert True

@given_election_testdir()
def test_election_property_3(testdir: ElectionTestDir):
    assert True

@given_election_testdir()
def test_election_property_3(testdir: ElectionTestDir):
    assert True

@given_election_testdir()
def test_election_property_4(testdir: ElectionTestDir):
    assert True

@given_election_testdir()
def test_election_property_5(testdir: ElectionTestDir):
    assert True


if __name__ == '__main__':
   args = ['pytest', 'test.py', '-vv']
   subprocess.check_call(args)
