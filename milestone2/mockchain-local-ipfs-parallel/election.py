#!/usr/bin/env python3

import click
import json
import logging
import subprocess
import time
import random
import sys

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

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from collections import defaultdict


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

def parse_config(cfg_path, pause_to_explain, random_seed):
    cfg_path = realpath(cfg_path)
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
    cfg.project_config = cfg_path # for passing to arion as an env var
    cfg.random_seed = random_seed
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
    container_name = cfg.arion.project_name + "-" + container_role + str(container_number) + "-egpy-1"
    script_path = join(cfg.arion.bind_mounts.scripts, script_name)
    args = ["docker", "exec", container_name,
            "poetry", "run", script_path] + args
    kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    log.info(' '.join(args))
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    # TODO remove stderr here since it's merged into stdout anyway?
    if stderr is not None:
        stderr = stderr.strip()
        if len(stderr) > 0:
            log.info(stderr + '\n')
    stdout = stdout.strip()
    if return_stdout:
        return stdout
    else:
        if len(stdout) > 0:
            log.info(stdout + '\n')
        return proc.returncode

@dataclass
class ContainerTask:
    script_name: str
    container_role: str
    container_number: int
    args: list
    kwargs: dict | None = None   # extra kwargs for run_in_container if needed

def run_many_in_containers(
    cfg,
    log,
    tasks,
    max_workers=16, # TODO default to nproc? nproc/2?
    return_stdout=False,
):
    """
    Run a batch of run_in_container calls in parallel, but serialize tasks
    per (container_role, container_number).
    """
    tasks = list(tasks)

    # One lock per container -> ensures only one task per container at a time
    container_locks: dict[tuple[str, int], Lock] = defaultdict(Lock)

    # If no max_workers specified, default to number of distinct containers
    if max_workers is None:
        containers = {
            (t.container_role, t.container_number)
            for t in tasks
        }
        max_workers = len(containers) or 1

    def _worker(t: ContainerTask):
        key = (t.container_role, t.container_number)
        lock = container_locks[key]

        with lock:   # serialize all tasks for this container
            kw = dict(t.kwargs or {})
            kw.setdefault("return_stdout", return_stdout)
            return run_in_container(
                cfg,
                log,
                t.script_name,
                t.container_role,
                t.container_number,
                t.args,
                **kw,
            )

    results = [None] * len(tasks)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_worker, t): idx for idx, t in enumerate(tasks)}

        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()

    return results


# TODO where should this go? utils.py?
def egsync_api_url(cfg, container_role, container_number):
    egsync_container = \
      cfg['arion']['project_name'] + \
      '-' + container_role + str(container_number) + '-egsync-1'
    api_url = f'http://{egsync_container}:5000/api' # TODO no /api? TODO 5001?
    # print(f'api_url: {api_url}')
    return api_url

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

    # Only needed when a previous run was inturrupted
    run_process(cfg, log, ['arion', 'down'])

    # For some reason this occassionally fails with a Docker "network not found" error.
    # The hacky solution seems to work: turning it off and on again.

    for retry in range(1, 4):
        time.sleep(retry * 2) # delay 2, 4, 6, 8 sec
        try:
            run_process(cfg, log, ['arion', 'up', '-d', '--remove-orphans'])
            return
        except Exception as e:
            log.error(f'arion up failed {retry+1} times: {e}')
            teardown(cfg, log)
    raise Exception('arion up failed too many times')

@explain_step
def teardown(cfg, log):
    run_process(cfg, log, ['arion', 'down'])

### election ###

@explain_step
def build_manifest(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "build-manifest",
            "--egsync-api", egsync_api_url(cfg, 'admin', 1),
            "--referendum-question", cfg.votes[0].question,
        ]
    )

@explain_step
def mint_guardian_channels(cfg, log):
    for guardian_id in cfg.election.guardians.ids:
        run_in_container(
            cfg, log, "admin.py", "admin", 1,
            [
                "mint-channel",
                "--egsync-api", egsync_api_url(cfg, 'admin', 1),
                "--channel-name", guardian_id
            ]
        )

@explain_step
def mint_verifier_channels(cfg, log):
    for n in range(1, cfg.election.verifiers.count+1):
        verifier_id = 'verifier_' + str(n)
        run_in_container(
            cfg, log, "admin.py", "admin", 1,
            [
                "mint-channel",
                "--egsync-api", egsync_api_url(cfg, 'admin', 1),
                "--channel-name", verifier_id
            ]
        )

@explain_step
def announce_key_ceremony(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "announce-key-ceremony",
            "--egsync-api", egsync_api_url(cfg, 'admin', 1),
            "--guardian-count", str(cfg.election.guardians.count),
            "--guardian-quorum", str(cfg.election.guardians.quorum),
        ]
    )

def key_ceremony_round(cfg, log, ceremony_round):
    tasks = []
    for guardian_id, sequence_order in zip(
        cfg.election.guardians.ids,
        cfg.election.guardians.sequence_order,
    ):
        tasks.append(
            ContainerTask(
                script_name="guardian.py",
                container_role="guardian",
                container_number=sequence_order,
                args=[
                    "key-ceremony",
                    "--egsync-api", egsync_api_url(cfg, "guardian", sequence_order),
                    "--private-dir", cfg.arion.bind_mounts.private,
                    "--ceremony-round", str(ceremony_round),
                    "--guardian-id", guardian_id,
                    "--guardian-sequence-order", str(sequence_order),
                ],
            )
        )

    results = run_many_in_containers(cfg, log, tasks)

    # Optional: check return codes
    for (guardian_id, seq), rc in zip(
        zip(cfg.election.guardians.ids, cfg.election.guardians.sequence_order),
        results,
    ):
        if rc != 0:
            log.warning(
                f"key ceremony round {ceremony_round} failed for guardian "
                f"{guardian_id} (sequence {seq}) with return code {rc}"
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
            "--egsync-api", egsync_api_url(cfg, 'admin', 1),
        ]
    )

@explain_step
def build_election(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "build-election",
            "--egsync-api", egsync_api_url(cfg, 'admin', 1),
        ]
    )

@explain_step
def mint_device_channels(cfg, log):
    for device_number in range(1, cfg.election.devices.count + 1):
        run_in_container(
            cfg, log, "admin.py", "admin", 1,
            [
                "mint-channel",
                "--egsync-api", egsync_api_url(cfg, 'admin', 1),
                "--channel-name", 'device_' + str(device_number)
            ]
        )

def add_device(cfg, log, device_number):
    return run_in_container(
        cfg, log, "device.py", "device", device_number,
        [
            "add-device",
            "--egsync-api", egsync_api_url(cfg, "device", device_number),
            "--device-number", str(device_number),
        ],
    )

@explain_step
def add_devices(cfg, log):
    tasks = []
    for device_number in range(1, cfg.election.devices.count + 1):
        tasks.append(
            ContainerTask(
                script_name="device.py",
                container_role="device",
                container_number=device_number,
                args=[
                    "add-device",
                    "--egsync-api", egsync_api_url(cfg, "device", device_number),
                    "--device-number", str(device_number),
                ],
            )
        )

    results = run_many_in_containers(cfg, log, tasks)

    for device_number, rc in zip(
        range(1, cfg.election.devices.count + 1), results
    ):
        if rc != 0:
            log.warning(f"add-device failed for device {device_number} with return code {rc}")

def vote_commit_task(cfg, device_number, candidate) -> ContainerTask:
    return ContainerTask(
        script_name="device.py",
        container_role="device",
        container_number=device_number,
        args=[
            "vote_commit",
            "--egsync-api", egsync_api_url(cfg, "device", device_number),
            "--private-dir", cfg.arion.bind_mounts.private,
            "--device-number", str(device_number),
            "--candidate", candidate,
        ],
        kwargs={"return_stdout": True},   # optional; can also pass via run_many_in_containers
    )

def vote_reveal_task(cfg, device_number, ballot_id, spoil=False) -> ContainerTask:
    return ContainerTask(
        script_name="device.py",
        container_role="device",
        container_number=device_number,
        args=[
            "vote_reveal",
            "--egsync-api", egsync_api_url(cfg, "device", device_number),
            "--private-dir", cfg.arion.bind_mounts.private,
            "--device-number", str(device_number),
            "--ballot-id", ballot_id,
            "--spoil", str(spoil),
        ],
    )

@explain_step
def vote_commit_all(cfg, log):
    votes_so_far = 0
    tasks = []

    for contest in cfg.votes:
        for (candidate, n_votes) in contest.answers.items():

            for _ in range(n_votes.spoil):
                device_number = votes_so_far % cfg.election.devices.count + 1
                tasks.append(vote_commit_task(cfg, device_number, candidate))
                votes_so_far += 1

            for _ in range(n_votes.cast):
                device_number = votes_so_far % cfg.election.devices.count + 1
                tasks.append(vote_commit_task(cfg, device_number, candidate))
                votes_so_far += 1

    ballot_ids = run_many_in_containers(
        cfg, log, tasks,
        return_stdout=True,   # also set in kwargs above; either is fine
    )

    for i, ballot_id in enumerate(ballot_ids):
        assert ballot_id, f"Empty ballot_id at index {i}"

    return ballot_ids


@explain_step
def vote_reveal_all(cfg, log, ballot_ids):
    votes_so_far = 0
    tasks = []

    for contest in cfg.votes:
        for (candidate, n_votes) in contest.answers.items():

            for _ in range(n_votes.spoil):
                device_number = votes_so_far % cfg.election.devices.count + 1
                ballot_id = ballot_ids[votes_so_far]
                tasks.append(vote_reveal_task(cfg, device_number, ballot_id, spoil=True))
                votes_so_far += 1

            for _ in range(n_votes.cast):
                device_number = votes_so_far % cfg.election.devices.count + 1
                ballot_id = ballot_ids[votes_so_far]
                tasks.append(vote_reveal_task(cfg, device_number, ballot_id, spoil=False))
                votes_so_far += 1

    assert votes_so_far == len(ballot_ids)

    results = run_many_in_containers(cfg, log, tasks)

    for i, rc in enumerate(results):
        if rc is not None and rc != 0:
            log.warning(f"vote_reveal failed for index {i} with return code {rc}")

@explain_step
def tally(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "tally",
            "--egsync-api", egsync_api_url(cfg, 'admin', 1),
        ]
    )

def decrypt_shares_task(cfg, guardian_id, sequence_order) -> ContainerTask:
    return ContainerTask(
        script_name="guardian.py",
        container_role="guardian",
        container_number=sequence_order,
        args=[
            "decrypt-shares",
            "--egsync-api", egsync_api_url(cfg, "guardian", sequence_order),
            "--private-dir", cfg.arion.bind_mounts.private,
            "--guardian-id", guardian_id,
        ],
    )

@explain_step
def decrypt_shares(cfg, log):
    tasks = []
    for guardian_id, sequence_order in zip(
        cfg.election.guardians.ids,
        cfg.election.guardians.sequence_order,
    ):
        tasks.append(decrypt_shares_task(cfg, guardian_id, sequence_order))

    results = run_many_in_containers(cfg, log, tasks)

    # Optional: check return codes
    for (guardian_id, sequence_order), rc in zip(
        zip(cfg.election.guardians.ids, cfg.election.guardians.sequence_order),
        results,
    ):
        if rc != 0:
            log.warning(
                f"decrypt-shares failed for guardian {guardian_id} "
                f"(sequence {sequence_order}) with return code {rc}"
            )

@explain_step
def decrypt_results(cfg, log):
    run_in_container(
        cfg, log, "admin.py", "admin", 1,
        [
            "decrypt-results",
            "--egsync-api", egsync_api_url(cfg, 'admin', 1),
        ]
    )

@explain_step
def verify(cfg, log):
    verifiers = sorted(
        [('verifier', n) for n in range(1, cfg.election.verifiers.count + 1)] +
        [('guardian', n) for n in range(1, cfg.election.guardians.count + 1)] +
        [('admin', 1)]
    )

    tasks = []
    for (container_role, container_number) in verifiers:
        verifier_id = f'{container_role}_{container_number}'
        logfile = join(
            cfg.arion.bind_mounts.private,
            f'{verifier_id}_verify.log'
        )

        tasks.append(
            ContainerTask(
                script_name="verifier.py",
                container_role=container_role,
                container_number=container_number,
                args=[
                    "verify",
                    "--egsync-api", egsync_api_url(cfg, container_role, container_number),
                    "--verifier-id", verifier_id,
                    "--logfile", logfile,
                ],
            )
        )

    # By default, max_workers == number of distinct containers in `tasks`
    results = run_many_in_containers(cfg, log, tasks)

    for (role, num), rc in zip(verifiers, results):
        if rc != 0:
            log.warning(f"verify failed for {role} {num} with return code {rc}")

# removed until I think how (or whether) to integrate attacks with ipfs + on-chain files
# @explain_step
# def attack(cfg, log: logging.Logger, fn_name: str, role: str, step: str, seed: int):
#     # attack specifies a role, but not the exact container
#     # so we choose which one to corrupt randomly here
#     counts = {
#         'admin'    : 1,
#         'verifier' : cfg.election.verifiers.count,
#         'guardian' : cfg.election.guardians.count,
#         'device'   : cfg.election.devices.count,
#     }
#     n = random.randint(1, counts[role])
#     logfile = join(cfg.arion.bind_mounts.private, 'attack.log')
#     run_in_container(
#         cfg, log, "attack.py", role, n,
#         [
#             "attack",
#             "--egsync-api", egsync_api_url(cfg, role, n),
#             "--private-dir", cfg.arion.bind_mounts.private,
#             "--logfile", logfile,
#             "--attack-fn", fn_name,
#             "--step", step,
#             "--random-seed", str(seed),
#         ]
#     )

# removed until I think how (or whether) to integrate attacks with ipfs + on-chain files
# def attack_all(cfg, log, step):
#     "Run any attack functions that target the current step"
#     for i in range(1, len(cfg.attacks) + 1):
#         fn_name = cfg.attacks[i-1]
#         attack_cfg = ATTACKS[fn_name]
#         if not step in attack_cfg['when']:
#             continue
#
#         # TODO is this reasonable?
#         # we mainly want to make sure that when the same attack is repeated in the same config,
#         # it doesn't use the same seed
#         seed = cfg.random_seed + i
#
#         attack(cfg, log, fn_name, attack_cfg['who'], step, seed)

def election(cfg, log) -> int:
    try:
        # TODO when should these happen?
        # TODO should they all be one mint_channels step?
        mint_guardian_channels(cfg, log)
        mint_verifier_channels(cfg, log)
        mint_device_channels(cfg, log)

        build_manifest(cfg, log)        # ; attack_all(cfg, log, 'build_manifest')
        announce_key_ceremony(cfg, log) # ; attack_all(cfg, log, 'announce_key_ceremony')
        key_ceremony_round1(cfg, log)   # ; attack_all(cfg, log, 'key_ceremony_round1')
        key_ceremony_round2(cfg, log)   # ; attack_all(cfg, log, 'key_ceremony_round2')
        key_ceremony_round3(cfg, log)   # ; attack_all(cfg, log, 'key_ceremony_round3')
        publish_joint_key(cfg, log)     # ; attack_all(cfg, log, 'publish_joint_key')
        build_election(cfg, log)        # ; attack_all(cfg, log, 'build_election')
        add_devices(cfg, log)           # ; attack_all(cfg, log, 'add_devices')
        ids = vote_commit_all(cfg, log) # ; attack_all(cfg, log, 'vote_commit_all')
        vote_reveal_all(cfg, log, ids)  # ; attack_all(cfg, log, 'vote_reveal_all')
        tally(cfg, log)                 # ; attack_all(cfg, log, 'tally')
        decrypt_shares(cfg, log)        # ; attack_all(cfg, log, 'decrypt_shares')
        decrypt_results(cfg, log)       # ; attack_all(cfg, log, 'decrypt_results')
    except Exception as e:
        print(e)
    finally:
        n_errors = verify(cfg, log) # ; attack_all(cfg, log, 'verify')
        time.sleep(3) # TODO do verifications ever fail to propagate?
        return n_errors

def main(cfg, log):
    try:
        setup(cfg, log)
        code = election(cfg, log)
    except Exception as e:
        log.error(e)
        log.error('Election failed :(')
        code = 1
    finally:
        teardown(cfg, log)
        sys.exit(code)


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
@click.option(
    "--random-seed",
    prompt="Random seed",
    help="Explicit random seed for debugging",
    type=click.INT,
)
def ElectionCommand(
    project_config: str,
    pause_to_explain: bool,
    random_seed: int,
    single_step: Optional[str],
    logfile: Optional[str],
) -> None:
    """Run an election with some options in a JSON config file.
    """
    cfg = parse_config(project_config, pause_to_explain, random_seed)
    log = init_log(cfg, logfile, logging.INFO)
    if single_step:
        run_single_step(cfg, log, single_step)
        # attack_all(cfg, log, single_step)
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

def hash_config(cfg: RunConfig, truncate=99) -> (int, str):
    "Ensures tmpdirs are not being reused after their configs change"
    s = str(cfg).encode('utf-8')
    h = hashlib.md5(s).digest().hex()
    int_hash = int(str(int(h, 16))[-truncate:])
    str_hash = h[:truncate]
    return (int_hash, str_hash)

ElectionTestDir = str

def run_test_election(cfg: RunConfig) -> ElectionTestDir:

    # use our own custom tmpdir instead of TemporaryDirectory
    (random_seed, h5) = hash_config(cfg, truncate=5)
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

        cfg = parse_config(cfg_path, pause_to_explain=False, random_seed=random_seed)
        log = init_log(cfg, logfile, logging.INFO)
        log.info(f'using random_seed from config hash: {random_seed}\n')
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
    # Random seed can be set per dev session, which offers a good
    # balance between caching and making sure different values work.
    # This is the top level main seed. It controls which random configs
    # hypothesis generates, and the hashes of the configs control the
    # downstream attack random seeds.
    # TODO is there a less confusing way to do that?
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
def given_election(attack_cfg_fn, max_examples: int):
    return yad([
        seed(get_random_seed()),
        settings(
            derandomize=False,
            max_examples=max_examples,
            deadline=None,
            phases=(Phase.explicit, Phase.reuse, Phase.generate),
        ),
        given(cfg=attack_cfg_fn()),
        prerun_test_election,
    ])

def given_honest_election(max_examples=10):
    return given_election(
        honestrun,
        max_examples=max_examples
    )

# def given_attacked_election(
#     attack: Optional[str] = None,
#     max_examples: Optional[int] = None
# ):
#
#     # Override attack_cfg if given explicitly.
#     # See test_withhold_manifest_attack below for an example.
#     if attack is None:
#
#         if max_examples is None:
#             max_examples = 10
#
#         def attackrun2(*args, **kwargs):
#             return attackrun(*args, **kwargs)
#
#     else:
#
#         # since we're only dealing with one attack,
#         # we probably don't need as many examples
#         if max_examples is None:
#             max_examples = 3
#
#         def attackrun2(*args, **kwargs):
#             kwargs.update(explicit_cfg=[attack])
#             return attackrun(*args, **kwargs)
#
#     return given_election(
#         attackrun2,
#         max_examples=max_examples
#     )


### misc small test helpers ###

def load_json(json_path: str):
    with open(json_path, 'r') as f:
        return json.load(f)

# TODO should this convert to a RunConfig instead?
def load_config_json(testdir: str) -> dict:
    json_path = join(testdir, 'election.json')
    json_dict = load_json(json_path)
    return json_dict

# TODO get via api instead
def load_verifier_json(testdir: str, verifier_id: str) -> dict:
    # TODO get via api instead
    json_path = join(testdir, f'data/private/{verifier_id}/egsync/4_verify/{verifier_id}.json')
    return load_json(json_path)

def election_verified(testdir: str, verifier_id: str) -> bool:
    try:
        summary = load_verifier_json(testdir, verifier_id)
        return summary['Verified']['gather_election']
    except:
        return False


### honest election property tests ###

def verifier_json_paths(testdir):
    # guardian_1 isn't special here; could use any verifier
    return sorted(glob(join(testdir, 'data/private/guardian_1/egsync/4_verify/*.json')))

# TODO rename something less confusing?
@given_honest_election()
def test_honest_always_verified(testdir: ElectionTestDir):
    json_paths = verifier_json_paths(testdir)
    n_verifications = len(json_paths)
    assert n_verifications > 0

@given_honest_election()
def test_honest_all_verifiers_agree_exactly(testdir: ElectionTestDir):
    first_summary: Optional[dict] = None
    json_paths = verifier_json_paths(testdir)
    for json_path in json_paths:
        summary = load_json(json_path)
        if first_summary is None:
            first_summary = summary
        else:
            assert summary == first_summary

@given_honest_election()
def test_honest_n_verifications_matches_cfg(testdir: ElectionTestDir):
    config = load_config_json(testdir)
    n_expected = sum([
        1, # admin
        config['election']['guardians']['count'],
        config['election']['verifiers']['count'],
    ])
    json_paths = verifier_json_paths(testdir)
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
        for (answer, n_spoiled) in sorted(contest['answers'].items()):
            # remove zero-vote candidates and contests to match summary-derived ones below
            if n_spoiled > 0:
                if not q in totals:
                    totals[q] = {}
                totals[q][answer] = n_spoiled
    return totals

@given_honest_election()
def test_honest_cast_votes_match_config(testdir: ElectionTestDir):

    cfg = load_config_json(testdir)
    expected_cast_totals = cast_vote_totals_from_config(cfg)

    # guardian_1 isn't special here; could use any verifier
    summary = load_verifier_json(testdir, 'guardian_1')
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
def test_honest_spoiled_votes_match_config(testdir: ElectionTestDir):

    cfg = load_config_json(testdir)
    expected_spoiled_totals = spoiled_vote_totals_from_config(cfg)
    note(f'expected_spoiled_totals: {expected_spoiled_totals}')

    # guardian_1 isn't special here; could use any verifier
    summary = load_verifier_json(testdir, 'guardian_1')
    actual_spoiled_totals = spoiled_vote_totals_from_summary(summary)
    note(f'actual_spoiled_totals: {actual_spoiled_totals}')

    assert actual_spoiled_totals == expected_spoiled_totals


### honest election property tests delegated to verifiers ###

def assert_verifiers_verified(testdir: ElectionTestDir, target_name: str, expected: bool = True):
    # TODO get via api instead
    # TODO also this is going to load all the verifications multiple times until you do
    json_paths = verifier_json_paths(testdir)
    assert len(json_paths) > 0 # exact number tested separately
    for json_path in json_paths:
        summary = load_json(json_path)
        verifier_id = splitext(basename(json_path))[0]
        actual = summary['Verified'][target_name]
        if actual != expected:
            msg = f'{verifier_id} verified {target_name}? {actual} but should be {expected}'
            raise Exception(msg)

@given_honest_election()
def test_honest_manifest_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'manifest')

@given_honest_election()
def test_honest_ceremony_details_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'ceremony_details')

@given_honest_election()
def test_honest_gather_announce_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_announce')

@given_honest_election()
def test_honest_all_guardian_backups_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_guardian_backups')

@given_honest_election()
def test_honest_all_guardian_verifications_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_guardian_verifications')

@given_honest_election()
def test_honest_gather_ceremony_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_ceremony')

@given_honest_election()
def test_honest_joint_key_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'joint_key')

@given_honest_election()
def test_honest_build_election_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'build_election')

@given_honest_election()
def test_honest_constants_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'constants')

# TODO remove?
# @given_honest_election()
# def test_honest_internal_manifest_verified(testdir: ElectionTestDir):
#   assert_verifiers_verified(testdir, 'internal_manifest')

@given_honest_election()
def test_honest_context_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'context')

@given_honest_election()
def test_honest_gather_constants_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_constants')

@given_honest_election()
def test_honest_all_devices_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_devices')

@given_honest_election()
def test_honest_gather_config_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_config')

@given_honest_election()
def test_honest_all_ballots_submitted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_ballots_submitted')

@given_honest_election()
def test_honest_all_ballots_cast_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_ballots_cast')

@given_honest_election()
def test_honest_all_ballots_spoiled_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_ballots_spoiled')

@given_honest_election()
def test_honest_all_spoiled_results_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'all_spoiled_results')

@given_honest_election()
def test_honest_n_spoiled_decrypted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'n_spoiled_decrypted')

@given_honest_election()
def test_honest_n_cast_spoiled_submitted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'n_cast_spoiled_submitted')

@given_honest_election()
def test_honest_set_spoiled_decrypted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'set_spoiled_decrypted')

@given_honest_election()
def test_honest_set_cast_spoiled_submitted_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'set_cast_spoiled_submitted')

@given_honest_election()
def test_honest_ballot_sets_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'ballot_sets')

@given_honest_election()
def test_honest_ciphertext_tally_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'ciphertext_tally')

@given_honest_election()
def test_honest_tally_aggregation_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'tally_aggregation')

@given_honest_election()
def test_honest_plaintext_tally_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'plaintext_tally')

@given_honest_election()
def test_honest_tally_decryption_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'tally_decryption')

@given_honest_election()
def test_honest_gather_tally_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_tally')

@given_honest_election()
def test_honest_gather_decryptions_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_decryptions')

@given_honest_election()
def test_honest_gather_election_verified(testdir: ElectionTestDir):
  assert_verifiers_verified(testdir, 'gather_election')


### test specific attacks ###

# def assume_successful_attack(testdir: ElectionTestDir):
#     """Assume that the attack(s) went through and should have some affect on
#     the results. Sometimes an attack is aborted instead, and then we wouldn't
#     expect the verifiers to notice anything. For example if it targets spoiled
#     votes and there weren't any broadcast from the corrupted device.
#     """
#     # TODO double check that all attacks print 'aborted' when they abort
#     attack_logs = glob(join(testdir, 'data/private/*/attack.log'))
#     n_non_aborted = 0
#     for attack_log in attack_logs:
#         with open(attack_log, 'r') as f:
#             txt = f.read()
#             if not 'abort' in txt:
#                 n_non_aborted += 1
#     assume(n_non_aborted > 0)
#
# def assert_verifiers_reject(testdir: ElectionTestDir, targets: List[str]):
#     "Assert that the test election verifiers did not verify any of these targets"
#     for target in targets:
#         assert_verifiers_verified(testdir, target, False)
#
# @pytest.mark.skip
# @given_attacked_election('admin_withhold_manifest')
# def test_attack_admin_withhold_manifest(testdir: ElectionTestDir):
#     assert_verifiers_reject(testdir, [
#         'manifest',
#         # ...
#         # other things should fail too,
#         # but we don't need to put them all
#         # ...
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('admin_ghost_after_vote')
# def test_attack_admin_ghost_after_vote(testdir: ElectionTestDir):
#     assert_verifiers_reject(testdir, [
#         'ciphertext_tally',
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('device_withhold_submitted_ballot')
# def test_attack_device_withhold_submitted_ballot(testdir: ElectionTestDir):
#     assert_verifiers_reject(testdir, [
#         'set_cast_spoiled_submitted',
#         'ballot_sets',
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('device_withhold_cast_ballot')
# def test_attack_device_withhold_cast_ballot(testdir: ElectionTestDir):
#     assume_successful_attack(testdir)
#     assert_verifiers_reject(testdir, [
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('device_withhold_spoiled_ballot')
# def test_attack_device_withhold_spoiled_ballot(testdir: ElectionTestDir):
#     assume_successful_attack(testdir)
#     assert_verifiers_reject(testdir, [
#         'set_cast_spoiled_submitted',
#         'ballot_sets',
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('device_mutate_submitted_ballot', max_examples=50)
# def test_attack_device_mutate_submitted_ballot(testdir: ElectionTestDir):
#     assert_verifiers_reject(testdir, [
#         'all_ballots_submitted',
#
#         # The tally will still validate if the mutated ballot was spoiled rather than cast
#         # 'ciphertext_tally',
#
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('device_mutate_spoiled_ballot', max_examples=50)
# def test_attack_device_mutate_spoiled_ballot(testdir: ElectionTestDir):
#     assume_successful_attack(testdir)
#     assert_verifiers_reject(testdir, [
#         # TODO others
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('guardian_withhold_tally_share')
# def test_attack_guardian_withhold_tally_share(testdir: ElectionTestDir):
#     assume_successful_attack(testdir)
#     assert_verifiers_reject(testdir, [
#         'plaintext_tally',
#         'tally_decryption',
#         'gather_election',
#     ])
#
# @pytest.mark.skip
# @given_attacked_election('guardian_withhold_spoiled_share')
# def test_attack_guardian_withhold_spoiled_share(testdir: ElectionTestDir):
#     assume_successful_attack(testdir)
#     assert_verifiers_reject(testdir, [
#         'all_spoiled_results',
#         'gather_election',
#     ])
#
#
# ### test attacks in general ###
#
# # TODO are there other cases when the election can still be verified?
# @pytest.mark.skip
# @given_attacked_election()
# def test_verifiers_notice_attacks(testdir: ElectionTestDir):
#     assume_successful_attack(testdir)
#     assert_verifiers_reject(testdir, ['gather_election'])
#
# @pytest.mark.skip
# @given_attacked_election()
# def test_attacks_are_logged(testdir: ElectionTestDir):
#     '''there should be at least 1 private attack.log,
#     and at least one attack mentioned in the main election.log
#     '''
#     attack_logs = glob(join(testdir, 'data/private/*/attack.log'))
#     assert len(attack_logs) > 0
#     with open(join(testdir, 'election.log'), 'r') as f:
#         main_log_txt = f.read() # TODO need to decode as utf-8?
#     assert 'attack.py' in main_log_txt
