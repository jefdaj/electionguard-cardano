#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import string
import logging
import tempfile
import hashlib

from hypothesis import given, settings

from config import *
from election import main, init_log, parse_config

TESTS_DIR = './tests'

def hash_config(cfg: ProjectConfig, truncate=99) -> str:
    "Ensures tmpdirs are not being reused after their configs change"
    s = str(cfg).encode('utf-8')
    d = hashlib.md5(s).digest()
    return d.hex()[:truncate]

def run_test_election(cfg: ProjectConfig):

    # use our own custom tmpdir instead of TemporaryDirectory
    h5 = hash_config(cfg, truncate=5)
    test_name = f'test_{h5}'
    tmpdir = os.path.join(TESTS_DIR, test_name)

    # experimental test strategy: only do the long election operation once,
    # then re-use the tmpdir for multiple assertions
    if os.path.exists(tmpdir):
        return

    try:
        os.makedirs(tmpdir)

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

# trivial first assertion to make sure run_test_election succeeds
@given(cfg=projectconfig())
@settings(max_examples=3, deadline=None)
def test_run_election(cfg: ProjectConfig):
    run_test_election(cfg)
    assert True


# TODO clean this up
if __name__ == '__main__':
   args = ['pytest', 'config.py', 'test.py', '-vvv']
   subprocess.check_call(args)
