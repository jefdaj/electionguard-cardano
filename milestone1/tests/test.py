#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import string
import logging
import tempfile
import hashlib
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
    test_name = f'test_{h5}'
    tmpdir = os.path.join(TESTS_DIR, test_name)

    # experimental test strategy: only do the long election operation once,
    # then re-use the tmpdir for multiple assertions
    lockfile = os.path.join(tmpdir, 'lock')
    if os.path.exists(tmpdir):
        # if another instance is running, wait for it to finish
        while os.path.exists(lockfile):
            time.sleep(1)
        # TODO check for error here
        return

    try:
        os.makedirs(tmpdir)
        lock = open(lockfile, 'w')

        data_dir = os.path.join(tmpdir, cfg['arion']['data_dir'])
        logfile  = os.path.join(tmpdir, 'election.log')

        os.makedirs(data_dir, exist_ok=False) # TODO remove?

        # TODO try leaving it as 'data' and finding the actual full path inside election.py from that
        cfg['arion']['data_dir'] = data_dir

        cfg_path = os.path.join(tmpdir, 'election.json') # TODO rename config?
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f)

        cfg = parse_config(cfg_path, pause_to_explain=False)
        log = init_log(logfile, logging.INFO)
        main(cfg, log)

    except:
        shutil.rmtree(tmpdir, ignore_errors=True)
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

# Convert a test that takes a cfg to one which takes a pre-run election with that cfg.
def with_prerun_election(fn):
    def wrapped(cfg: ProjectConfig, *args, **kwargs):
        tmpdir = run_test_election(cfg)
        return fn(tmpdir, *args, **kwargs)
    return wrapped

# A somewhat mind bending hack to make hypothesis reuse cached test elections.
# This way we can define a lot of rapid tests that make individual assertions about the results.
# Note that max_examples really is a max; hypothesis will often run fewer.
# TODO is this a partial solution to https://github.com/HypothesisWorks/hypothesis/issues/114
def given_cached_test_elections(max_examples=3):
    return yad([
        seed(0),
        settings(max_examples=max_examples, deadline=None),
        given(cfg=projectconfig()),
        with_prerun_election,
    ])


# TODO fill these out with useful properties

@given_cached_test_elections()
def test_election_property_1(testdir: ElectionTestDir):
    assert True

@given_cached_test_elections()
def test_election_property_2(testdir: ElectionTestDir):
    assert True

@given_cached_test_elections()
def test_election_property_3(testdir: ElectionTestDir):
    assert True

@given_cached_test_elections(7)
def test_election_property_3(testdir: ElectionTestDir):
    assert True

@given_cached_test_elections()
def test_election_property_4(testdir: ElectionTestDir):
    assert True

@given_cached_test_elections()
def test_election_property_5(testdir: ElectionTestDir):
    assert True


# TODO clean this up
if __name__ == '__main__':
   args = ['pytest', 'config.py', 'test.py', '-vvv']
   subprocess.check_call(args)
