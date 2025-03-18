#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import string
import logging
import tempfile

from hypothesis import given, settings

from config import *
from election import main, init_log, parse_config

TESTS_DIR = './tests'

@given(cfg=projectconfig())
@settings(max_examples=3, deadline=None)
def test_run_election(cfg: ProjectConfig):

    # use our own custom tmpdir isntead of TemporaryDirectory
    tmpdir = os.path.join(TESTS_DIR, cfg['arion']['project_name'])

    # experimental test strategy: only do the long election operation once,
    # then re-use the tmpdir for multiple assertions
    if not os.path.exists(tmpdir):
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


# TODO clean this up
if __name__ == '__main__':
   args = ['pytest', 'config.py', 'test.py', '-vvv']
   subprocess.check_call(args)
