#!/usr/bin/env python3

import json
import os
import pytest
import shutil
import subprocess
import string
import logging
import tempfile

from hypothesis import given, settings

from config import *
from election import main, init_log, parse_config

TESTS_DIR = './tests'

# Hacky way to ensure that the tempdir names are also valid for naming containers
# https://stackoverflow.com/a/12522964
# class RandomDigits(tempfile._RandomNameSequence):
#     characters = list(string.digits)
# 
# tempfile._name_sequence = RandomDigits()

# TODO why isn't it respecting max_examples?
@given(cfg=projectconfig())
@settings(max_examples=3, deadline=None)
def test_run_election(cfg: ProjectConfig):

    # use our own custom tmpdir isntead of TemporaryDirectory
    # TODO does that help?
    tmpdir = os.path.join(TESTS_DIR, cfg['arion']['project_name'])

    # experimental test strategy: only do the long election operation once,
    # then re-use the tmpdir for multiple assertions
    # TODO delete it if main exits non-zero though
    if not os.path.exists(tmpdir):
        try:
            os.makedirs(tmpdir)

            # with tempfile.TemporaryDirectory(dir=TESTS_DIR, prefix='test', delete=True, ignore_cleanup_errors=True) as tmpdir:
            # TODO does this help? can it be avoided?
            # subprocess.check_call(['sudo', 'chmod', '777', tmpdir, '-R'])

            data_dir = os.path.join(tmpdir, cfg['arion']['data_dir'])
            logfile  = os.path.join(tmpdir, 'election.log')

            os.makedirs(data_dir, exist_ok=False) # TODO remove?

            # TODO is this causing the tests to fail because it's nondeterministic?
            # TODO try leaving it as 'data' and finding the actual full path inside election.py from that
            cfg['arion']['data_dir'] = data_dir

            cfg_path = os.path.join(tmpdir, 'election.json') # TODO rename config?
            with open(cfg_path, 'w') as f:
                json.dump(cfg, f)

            cfg = parse_config(cfg_path, pause_to_explain=False)
            log = init_log(logfile, logging.INFO)
            main(cfg, log)

            # TODO other idea: maybe the exit code is nonzero
            # TODO other idea: maybe you should add some assertions here
            # TODO other idea: redirect all stdout to {data_dir}/election.log, then pass stdout from pytest

        except:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise

    # TODO does this help?
    assert True


if __name__ == '__main__':
   args = ['config.py', 'test.py', '-vvv']
   pytest.main(args)
