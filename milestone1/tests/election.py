#!/usr/bin/env python3

import click
import json
import logging
import subprocess
import time
import random

from click_default_group import DefaultGroup
from dotmap import DotMap
from os import environ
from os.path import join, exists, realpath, basename, dirname, splitext
from typing import Optional

import hashlib

from glob import glob
from hypothesis import given, settings, seed, Phase
import pytest
from sys import argv

from config import *

# TODO remove, or leave in for debugging?
from hypothesis import note


### utilities ###

def init_log(cfg, logfile, level=logging.WARNING):
    # unique name here is important to prevent test logs from mixing
    log = logging.getLogger(cfg.arion.project_name)
    log.setLevel(level)
    if logfile is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(logfile)
    # handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log

def parse_config(cfg_path, pause_to_explain):
    cfg_path = realpath(cfg_path)
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
    cfg.project_config = cfg_path # for passing to arion as an env var
    cfg.pause_to_explain = pause_to_explain
    # TODO do something like this per contest answers dict?
    # cfg.votes = dict(cfg.votes) # TODO is this the simplest way to enable iteration?
    ecfg = cfg.election
    ecfg.guardians.sequence_order = [*range(1, ecfg.guardians.count + 1)]
    ecfg.guardians.ids = [f"guardian_{i}" for i in ecfg.guardians.sequence_order]
    return cfg

# TODO args -> *args?
def run_in_container(
    cfg,
    log,
    script_name,
    container_role,
    container_number,
    args,
    return_stdout=False,
    **kwargs
):
    container_name = cfg.arion.project_name + "-" + container_role + str(container_number) + "-1"
    script_path = join(cfg.arion.bind_mounts.scripts, script_name)
    args = ["docker", "exec", container_name,
            "poetry", "run", script_path] + args
    kwargs.update(stdout=subprocess.PIPE, text=True)
    log.info(' '.join(args))
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    if stderr is not None:
        stderr = stderr.strip()
        if len(stderr) > 0:
            log.info(stderr)
    stdout = stdout.strip()
    if return_stdout:
        return stdout
    elif len(stdout) > 0:
        log.info(stdout)

def explain_step(fn):
    def decorated_fn(cfg, log, *args, **kwargs):
        header = f'### {fn.__name__} ###'
        log.info(header)
        if cfg.pause_to_explain:
            log.info('#  ')
            while True:
                if len(input('#  ').strip()) == 0:
                    log.info('#' * len(header) + '\n')
                    break
        log.info('')
        result = fn(cfg, log, *args, **kwargs)
        log.info('')
        return result
    return decorated_fn

def run_single_step(cfg, log, fn_name):
    fn = globals()[fn_name]
    fn(cfg, log)

def run_process(cfg, log, args):
    env = environ.copy()
    env['PROJECT_CONFIG'] = cfg.project_config
    proc = subprocess.Popen(
        args, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # TODO any easy way to interleave them?
    stdout, stderr = proc.communicate()
    msg = stdout + stderr
    msg = msg.strip()
    log.info(msg)
    if proc.returncode != 0:
        raise Exception(f'process returned {proc.returncode}')

@explain_step
def setup(cfg, log):
    # For some reason this occassionally fails with a Docker "network not found" error.
    # The hacky solution seems to work: turning it off and on again.
    for retry in range(1, 4):
        time.sleep(retry * 2) # delay 2, 4, 6, 8 sec
        try:
            run_process(cfg, log, ['arion', 'up', '-d'])
            return
        except Exception as e:
            log.error(f'arion up failed {retry+1} times: {e}')
            teardown(cfg, log)
    raise Exception('arion up failed too many times')

@explain_step
def teardown(cfg, log):
    run_process(cfg, log, ['arion', 'down'])
    # time.sleep(3) # TODO is this necessary?


### election ###

@explain_step
def build_manifest(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "build-manifest",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--referendum-question", cfg.votes[0].question,
        ]
    )

@explain_step
def announce_key_ceremony(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "announce-key-ceremony",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--guardian-count", str(cfg.election.guardians.count),
            "--guardian-quorum", str(cfg.election.guardians.quorum),
        ]
    )

def key_ceremony_round(cfg, log, ceremony_round):
    for guardian_id, sequence_order in \
            zip(cfg.election.guardians.ids, cfg.election.guardians.sequence_order):
        run_in_container(
            cfg, log, "guardian.py", "guardian", sequence_order,
            [
                "key-ceremony",
                "--public-dir", cfg.arion.bind_mounts.public,
                "--private-dir", cfg.arion.bind_mounts.private,
                "--ceremony-round", str(ceremony_round),
                "--guardian-id", guardian_id,
                "--guardian-sequence-order", str(sequence_order),
            ]
        )

@explain_step
def key_ceremony_round1(cfg, log):
    key_ceremony_round(cfg, log, 1)


@explain_step
def key_ceremony_round2(cfg, log):
    key_ceremony_round(cfg, log, 2)

@explain_step
def key_ceremony_round3(cfg, log):
    key_ceremony_round(cfg, log, 3)

@explain_step
def publish_joint_key(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "publish-joint-key",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

@explain_step
def build_election(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "build-election",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

def add_device(cfg, log, device_number):
    run_in_container(
        cfg, log, "device.py", "device", device_number,
        [
            "add-device",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--device-number", str(device_number),
        ]
    )

@explain_step
def add_devices(cfg, log):
    for n in range(1, cfg.election.devices.count + 1):
        add_device(cfg, log, n)

def vote_commit(cfg, log, device_number, candidate, spoil=False):
    "submit a ballot but don't say whether it's being cast or spoiled yet"
    ballot_id = run_in_container(
        cfg, log, "device.py", "device", device_number,
        [
            "vote_commit",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--private-dir", cfg.arion.bind_mounts.private,
            "--device-number", str(device_number),
            "--candidate", candidate,
        ],
        return_stdout=True
    )
    return ballot_id

def vote_reveal(cfg, log, device_number, ballot_id, spoil=False):
    "cast or spoil a previously submitted ballot"
    run_in_container(
        cfg, log, "device.py", "device", device_number,
        [
            "vote_reveal",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--private-dir", cfg.arion.bind_mounts.private,
            "--device-number", str(device_number),
            "--ballot-id", ballot_id,
            "--spoil", str(spoil),
        ]
    )

@explain_step
def vote_commit_all(cfg, log):
    votes_so_far = 0
    ballot_ids = []

    for contest in cfg.votes:

        # remember a "candidate" might also be an answer to a referendum question!
        # TODO have they come up with a better name for that in the 2.0 spec?
        for (candidate, n_votes) in contest.answers.items():

            for _ in range(n_votes.spoil):
                # hack to iterate over devices, just to show there can be more than one
                device_number = votes_so_far % cfg.election.devices.count + 1
                ballot_id = vote_commit(cfg, log, device_number, candidate, spoil=True)
                assert len(ballot_id) > 0
                votes_so_far += 1
                ballot_ids.append(ballot_id)

            for _ in range(n_votes.cast):
                device_number = votes_so_far % cfg.election.devices.count + 1
                ballot_id = vote_commit(cfg, log, device_number, candidate)
                assert len(ballot_id) > 0
                votes_so_far += 1
                ballot_ids.append(ballot_id)

    return ballot_ids

@explain_step
def vote_reveal_all(cfg, log, ballot_ids):

    # this time we use this to index in ballot_ids too
    votes_so_far = 0

    for contest in cfg.votes:
        for (candidate, n_votes) in contest.answers.items():

            for _ in range(n_votes.spoil):
                device_number = votes_so_far % cfg.election.devices.count + 1
                ballot_id = ballot_ids[votes_so_far]
                vote_reveal(cfg, log, device_number, ballot_id, spoil=True)
                votes_so_far += 1

            for _ in range(n_votes.cast):
                device_number = votes_so_far % cfg.election.devices.count + 1
                ballot_id = ballot_ids[votes_so_far]
                vote_reveal(cfg, log, device_number, ballot_id, spoil=False)
                votes_so_far += 1

    assert votes_so_far == len(ballot_ids)

@explain_step
def tally(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "tally",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

@explain_step
def decrypt_shares(cfg, log):
    for guardian_id, sequence_order in \
            zip(cfg.election.guardians.ids, cfg.election.guardians.sequence_order):
        run_in_container(
            cfg, log, "guardian.py", "guardian", sequence_order,
            [
                "decrypt-shares",
                "--public-dir", cfg.arion.bind_mounts.public,
                "--private-dir", cfg.arion.bind_mounts.private,
                "--guardian-id", guardian_id,
            ]
        )

@explain_step
def decrypt_results(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "decrypt-results",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

# @explain_step
# def summary(cfg):
#     run_in_container(
#         cfg, "admin", 1,
#         [
#             "summary",
#             "--public-dir", cfg.arion.bind_mounts.public,
#         ]
#     )

@explain_step
def verify(cfg, log):
    verifiers = sorted(
        [('verifier', n) for n in range(1, cfg.election.verifiers.count+1)] + \
        [('guardian', n) for n in range(1, cfg.election.guardians.count+1)] + \
        [('admin', 1)]
    )
    for (container_role, container_number) in verifiers:
        verifier_id = f'{container_role}_{container_number}'
        logfile = join(cfg.arion.bind_mounts.private, 'verify.log')
        run_in_container(
            cfg, log, "verifier.py", container_role, container_number,
            [
                "verify",
                "--public-dir", cfg.arion.bind_mounts.public,
                "--verifier-id", verifier_id,
                "--logfile", logfile,
            ]
        )

def attack(cfg, log, step):
    "Run any attack functions that target the current step"

    for i in range(1, len(cfg.attacks) + 1):
        attack = cfg.attacks[i-1]
        if not step in attack.when:
            continue

        seed = i # TODO should the test hash also contribute?

        # attack specifies a role, but not the exact container
        # so we choose which one to corrupt randomly here
        role = attack.who
        counts = {
            'admin'    : 1,
            'verifier' : cfg.verifiers.count,
            'guardian' : cfg.guardians.count,
            'device'   : cfg.devices.count,
        }
        random.seed(seed)
        n = random.randint(1, counts[role])

        logfile = join(cfg.arion.bind_mounts.private, 'attack.log')
        run_in_container(
            cfg, log, "attack.py", role, n,
            [
                "attack",
                "--public-dir", cfg.arion.bind_mounts.public,
                "--private-dir", cfg.arion.bind_mounts.private,
                "--logfile", logfile,
                "--attack-fn", attack.what,
                "--step", step,
                "--random-seed", str(seed),
            ]
        )

# TODO should the attacks be called as part of each step rather than separately?
def election(cfg, log):
    try:
        build_manifest(cfg, log)        ; attack(cfg, log, 'build_manifest')
        announce_key_ceremony(cfg, log) ; attack(cfg, log, 'announce_key_ceremony')
        key_ceremony_round1(cfg, log)   ; attack(cfg, log, 'key_ceremony_round1')
        key_ceremony_round2(cfg, log)   ; attack(cfg, log, 'key_ceremony_round2')
        key_ceremony_round3(cfg, log)   ; attack(cfg, log, 'key_ceremony_round3')
        publish_joint_key(cfg, log)     ; attack(cfg, log, 'publish_joint_key')
        build_election(cfg, log)        ; attack(cfg, log, 'build_election')
        add_devices(cfg, log)           ; attack(cfg, log, 'add_devices')
        ids = vote_commit_all(cfg, log) ; attack(cfg, log, 'vote_commit_all')
        vote_reveal_all(cfg, log, ids)  ; attack(cfg, log, 'vote_reveal_all')
        tally(cfg, log)                 ; attack(cfg, log, 'tally')
        decrypt_shares(cfg, log)        ; attack(cfg, log, 'decrypt_shares')
        decrypt_results(cfg, log)       ; attack(cfg, log, 'decrypt_results')
    except:
        pass
    finally:
        verify(cfg, log) ; attack(cfg, log, 'verify')

def main(cfg, log):
    try:
        setup(cfg, log)
        election(cfg, log)
    except Exception as e:
        log.error(e)
        log.error('Election failed :(')
    finally:
        teardown(cfg, log)


### cli ###

@click.command("election")
@click.option(
    "--project-config",
    help="Path to the JSON config file.",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default='election.json',
    show_default=True
)
@click.option(
    "--pause-to-explain",
    help="Pauses the script while you type comments before each important step.",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True
)
@click.option(
    "--single-step",
    help="Run just one step for easier debugging.",
    type=click.STRING,
    # TODO is removing prompt how you make it optional?
)
@click.option(
    "--logfile",
    prompt="Logfile (default: stdout)",
    help="Where to log printed messages",
    type=click.STRING,
)
def ElectionCommand(
    project_config: str,
    pause_to_explain: bool,
    single_step: Optional[str],
    logfile: Optional[str],
) -> None:
    """Run an election with some options in a JSON config file.
    """
    cfg = parse_config(project_config, pause_to_explain)
    log = init_log(cfg, logfile, logging.INFO)
    if single_step:
        run_single_step(cfg, log, single_step)
        attack(cfg, log, single_step)
    else:
        main(cfg, log)

@click.group(cls=DefaultGroup, default='election', default_if_no_args=True)
def cli() -> None:
    pass

cli.add_command(ElectionCommand)

if __name__ == '__main__':
    cli()


### tests ###

TESTS_DIR = './tests'

def hash_config(cfg: RunConfig, truncate=99) -> str:
    "Ensures tmpdirs are not being reused after their configs change"
    s = str(cfg).encode('utf-8')
    d = hashlib.md5(s).digest()
    return d.hex()[:truncate]

ElectionTestDir = str

def run_test_election(cfg: RunConfig) -> ElectionTestDir:

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
# TODO will this pass args and kwargs properly when chained via yad?
def prerun_test_election(fn_from_testdir):
    def fn_from_cfg(cfg: RunConfig, *args, **kwargs):
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
def given_election(attack_cfg_fn):
    return yad([
        seed(get_random_seed()),
        settings(
            # derandomize=True, # this is already default?
            max_examples=2,
            deadline=None,
            phases=(Phase.explicit, Phase.reuse, Phase.generate),
        ),
        given(cfg=attack_cfg_fn()),
        prerun_test_election,
    ])

def given_honest_election():
    return given_election(honestrun)

def given_attack_election():
    return given_election(attackrun)


### misc small test helpers ###

def load_json(json_path: str):
    with open(json_path, 'r') as f:
        return json.load(f)

# TODO should this convert to a RunConfig instead?
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
        return summary['Verified']['gather_election']
    except:
        return False


### property tests ###

# TODO rename something less confusing?
@given_honest_election()
def test_honest_election_finishes(testdir: ElectionTestDir):
    json_paths = glob(join(testdir, 'data/public/4_verify/*.json'))
    n_verifications = len(json_paths)
    assert n_verifications > 0

@given_honest_election()
def test_all_election_verifiers_agree_exactly(testdir: ElectionTestDir):
    first_summary: Optional[dict] = None
    json_paths = glob(join(testdir, 'data/public/4_verify/*.json'))
    for json_path in json_paths:
        summary = load_json(json_path)
        if first_summary is None:
            first_summary = summary
        else:
            assert summary == first_summary

@given_honest_election()
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
            # remove zero-vote candidates to match actual config
            if n_spoiled > 0:
                totals[q][answer] = n_spoiled
    return totals

@given_honest_election()
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

@given_honest_election()
def test_spoiled_votes_match_config(testdir: ElectionTestDir):

    cfg = load_config_json(testdir)
    expected_spoiled_totals = spoiled_vote_totals_from_config(cfg)
    # note(expected_spoiled_totals)

    # admin isn't special here; could use any verifier
    summary = load_summary_json(testdir, 'admin_1')
    actual_spoiled_totals = spoiled_vote_totals_from_summary(summary)
    # note(actual_spoiled_totals)

    assert actual_spoiled_totals == expected_spoiled_totals


### property tests delegated to verifiers ###

def assert_verifiers_verified(testdir: ElectionTestDir, target_name: str, expected: bool = True):
    json_paths = sorted(glob(join(testdir, 'data/public/4_verify/*.json')))
    assert len(json_paths) > 0 # exact number tested separately
    for json_path in json_paths:
        summary = load_json(json_path)
        verifier_id = splitext(basename(json_path))[0]
        actual = summary['Verified'][target_name]
        if actual != expected:
            msg = f'{verifier_id} verified {target_name}? {actual} but should be {expected}'
            raise Exception(msg)

@given_honest_election()
def test_manifest_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'manifest')

@given_honest_election()
def test_ceremony_details_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'ceremony_details')

@given_honest_election()
def test_gather_announce_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_announce')

@given_honest_election()
def test_all_guardian_backups_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_guardian_backups')

@given_honest_election()
def test_all_guardian_verifications_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_guardian_verifications')

@given_honest_election()
def test_gather_ceremony_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_ceremony')

@given_honest_election()
def test_joint_key_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'joint_key')

@given_honest_election()
def test_build_election_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'build_election')

@given_honest_election()
def test_constants_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'constants')

@given_honest_election()
def test_internal_manifest_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'internal_manifest')

@given_honest_election()
def test_context_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'context')

@given_honest_election()
def test_gather_constants_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_constants')

@given_honest_election()
def test_all_devices_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_devices')

@given_honest_election()
def test_gather_config_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_config')

@given_honest_election()
def test_all_ballots_submitted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_ballots_submitted')

@given_honest_election()
def test_all_ballots_cast_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_ballots_cast')

@given_honest_election()
def test_all_ballots_spoiled_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_ballots_spoiled')

@given_honest_election()
def test_all_spoiled_results_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_spoiled_results')

@given_honest_election()
def test_n_spoiled_decrypted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'n_spoiled_decrypted')

@given_honest_election()
def test_n_cast_spoiled_submitted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'n_cast_spoiled_submitted')

@given_honest_election()
def test_set_spoiled_decrypted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'set_spoiled_decrypted')

@given_honest_election()
def test_set_cast_spoiled_submitted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'set_cast_spoiled_submitted')

@given_honest_election()
def test_ballot_sets_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'ballot_sets')

@given_honest_election()
def test_ciphertext_tally_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'ciphertext_tally')

@given_honest_election()
def test_tally_aggregation_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'tally_aggregation')

@given_honest_election()
def test_plaintext_tally_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'plaintext_tally')

@given_honest_election()
def test_tally_decryption_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'tally_decryption')

@given_honest_election()
def test_gather_tally_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_tally')

@given_honest_election()
def test_gather_decryptions_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_decryptions')

@given_honest_election()
def test_gather_election_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_election')


### attack tests ###

# TODO more specific attacks as decorator args to enable this?
# @given_attack_election()
# def test_withhold_manifest_attack(testdir: ElectionTestDir):
#     assert_verifiers_verified(testdir, 'manifest', False)

# this isn't always true, but a reasonable first approximation
@given_attack_election()
def test_election_fails_when_attacked(testdir: ElectionTestDir):
    assert_verifiers_verified(testdir, 'gather_election', False)
