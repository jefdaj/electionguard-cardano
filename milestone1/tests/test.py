#!/usr/bin/env python3

import hashlib
import json
import logging
import os
import subprocess
import time

from glob import glob
from hypothesis import given, settings, seed, Phase
from os.path import join, exists
from sys import argv

from config import *
from election import main, init_log, parse_config

# TODO remove, or leave in for debugging?
# from hypothesis import note


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
    tmpdir = join(TESTS_DIR, test_name)

    # This should prevent more than one run_test_election from running with the
    # same config at the same time. Not sure whether that happens in practice,
    # but better to be safe than sorry when using pytest -n<threads>, right?
    # TODO why is it making only one election run at a time though?
    lockfile = join(tmpdir, 'election.lock')

    if exists(tmpdir):
        # if another instance is running, wait for it to finish
        while exists(lockfile):
            time.sleep(1)
        return tmpdir

    try:
        os.makedirs(tmpdir)
        lock = open(lockfile, 'w')

        data_dir = join(tmpdir, cfg['arion']['data_dir'])
        logfile  = join(tmpdir, 'election.log')

        os.makedirs(data_dir, exist_ok=False) # TODO remove?

        # TODO leave data_dir as 'data' and resolve inside election.py?
        cfg['arion']['data_dir'] = data_dir
        cfg['arion']['project_name'] = test_name

        cfg_path = join(tmpdir, 'election.json') # TODO rename config?
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f)

        cfg = parse_config(cfg_path, pause_to_explain=False)
        log = init_log(cfg, logfile, logging.INFO)
        main(cfg, log)

    except:
        # TODO rm here? or do we want to keep + inspect the error files?
        # shutil.rmtree(tmpdir, ignore_errors=True)
        # raise
        pass

    finally:
        try:
            lock.close()
            os.remove(lockfile)
        except:
            pass
        return tmpdir

# "yet another decorator"
# https://stackoverflow.com/a/4122845
def yad(decorators):
    def decorator(f):
        for d in reversed(decorators):
            f = d(f)
        return f
    return decorator

# Convert a test that takes a cfg to one which takes a pre-run election testdir
# generated from that cfg.
def prerun_test_election(fn_from_testdir):
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
# - prerun_test_election is a separate idea that was also convenient to tack on here
# - max_examples really is a max; hypothesis will often run fewer
#
# TODO is this a partial solution to https://github.com/HypothesisWorks/hypothesis/issues/114
# TODO top level CLI arg for max_examples here?
# TODO if no args needed, remove this def lambda
def given_election_testdir():
    return yad([
        seed(get_random_seed()),
        settings(
            # derandomize=True, # this is already default?
            max_examples=10,
            deadline=None,
            phases=(Phase.explicit, Phase.reuse, Phase.generate),
        ),
        given(cfg=projectconfig()),
        prerun_test_election,
    ])


### misc small test helpers ###

def load_json(json_path: str):
    with open(json_path, 'r') as f:
        return json.load(f)

# TODO should this convert to a ProjectConfig instead?
def load_config_json(testdir: str) -> dict:
    json_path = join(testdir, 'election.json')
    json_dict = load_json(json_path)
    return json_dict

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

# TODO rename something less confusing?
@given_election_testdir()
def test_election_finished(testdir: ElectionTestDir):
    json_paths = glob(join(testdir, 'data/public/4_verify/*.json'))
    n_verifications = len(json_paths)
    assert n_verifications > 0

@given_election_testdir()
def test_election_verified_by_admin(testdir: ElectionTestDir):
    assert election_verified(testdir, 'admin_1')

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
def test_n_verifications_matches_cfg(testdir: ElectionTestDir):
    config = load_config_json(testdir)
    n_expected = sum([
        1, # admin
        config['election']['guardians']['count'],
        config['election']['verifiers']['count'],
    ])
    json_paths = glob(join(testdir, 'data/public/4_verify/*.json'))
    n_actual = len(json_paths)
    assert n_actual == n_expected

def vote_totals_from_config(config, spoiled: bool):
    expected_contests = sorted(config['votes'])
    "Pull just the cast OR spoiled totals from the config"
    if spoiled:
        key = 'spoil'
    else:
        key = 'cast'
    simple_casts = []
    for contest in expected_contests:
        simple_cast = {
            'question': contest['question'],
            'answers': { k: v[key] for (k, v) in sorted(contest['answers'].items()) }
        }
        simple_casts.append(simple_cast)
    return simple_casts

def cast_vote_totals_from_config(contest_config):
    return vote_totals_from_config(contest_config, spoiled=False)

def spoiled_vote_totals_from_config(contest_config):
    totals_contest_list = vote_totals_from_config(contest_config, spoiled=True)
    # simplify to match the summary format
    totals = {}
    for contest in totals_contest_list:
        q = contest['question']
        if not q in totals:
            totals[q] = {}
        for (answer, n_spoiled) in sorted(contest['answers'].items()):
            totals[q][answer] = n_spoiled
    return totals

@given_election_testdir()
def test_cast_votes_match_config(testdir: ElectionTestDir):

    cfg = load_config_json(testdir)
    expected_cast_totals = cast_vote_totals_from_config(cfg)

    # admin isn't special here; could use any verifier
    summary = load_summary_json(testdir, 'admin_1')
    actual_cast_totals = sorted(summary['Final tally of cast ballots'])

    assert len(expected_cast_totals) == len(actual_cast_totals)
    for (expected, actual) in zip(expected_cast_totals, actual_cast_totals):

        assert set(expected['answers'].keys()) == set(actual['answers'].keys())

        for (answer, n_actual) in actual['answers'].items():
            assert n_actual == expected['answers'][answer]

def spoiled_vote_totals_from_summary(summary):
    ballots = summary['Individual spoiled ballots']
    totals = {}
    for (ballot_id, contests) in ballots.items():
        for contest in contests:
            for (question, answer) in sorted(contest.items()):
                if not question in totals:
                    totals[question] = {}
                if not answer in totals[question]:
                    totals[question][answer] = 0
                totals[question][answer] += 1
    return totals

@given_election_testdir()
def test_spoiled_votes_match_config(testdir: ElectionTestDir):

    cfg = load_config_json(testdir)
    expected_spoiled_totals = spoiled_vote_totals_from_config(cfg)

    # admin isn't special here; could use any verifier
    summary = load_summary_json(testdir, 'admin_1')
    actual_spoiled_totals = spoiled_vote_totals_from_summary(summary)

    assert actual_spoiled_totals == expected_spoiled_totals


### main ###

if __name__ == '__main__':
    args = ['pytest', 'test.py', '-v'] + argv[1:]
    subprocess.check_call(args)
