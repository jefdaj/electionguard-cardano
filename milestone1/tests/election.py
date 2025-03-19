#!/usr/bin/env python3

import click
import json
import logging
import subprocess
import time

from click_default_group import DefaultGroup
from dotmap import DotMap
from os import environ
from os.path import join, exists, realpath, basename, dirname
from typing import Optional


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
    cfg.votes = dict(cfg.votes) # TODO is this the simplest way to enable iteration?
    ecfg = cfg.election
    ecfg.guardians.sequence_order = [*range(1, ecfg.guardians.count + 1)]
    ecfg.guardians.ids = [f"guardian_{i}" for i in ecfg.guardians.sequence_order]
    return cfg

def run_in_container(cfg, log, script_name, container_role, container_number, args, **kwargs):
    container_name = cfg.arion.project_name + "-" + container_role + str(container_number) + "-1"
    script_path = join(cfg.arion.bind_mounts.scripts, script_name)
    # TODO python don't write bytecode (here or in the image?)
    args = ["docker", "exec", container_name,
            "poetry", "run", script_path] + args
    kwargs.update(stdout=subprocess.PIPE, text=True)
    log.info(' '.join(args))
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    stdout = stdout.strip()
    if len(stdout) > 0:
        log.info(stdout, flush=True) # TODO log?
    if stderr is not None:
        stderr = stderr.strip()
        if len(stderr) > 0:
            log.info(stderr, flush=True) # TODO log?

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
    fn(cfg)

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

# def arion_cleanup(cfg, log):
    # in case a previous run failed
    # TODO remove?
#     run_process(cfg, log, ['arion', 'down'])
    # TODO can Docker or Arion do this rm step more safely?
    # data_dir = './data'
    # if exists(data_dir):
    #     subprocess.check_call(['sudo', 'rm', '-rf', data_dir])

@explain_step
def setup(cfg, log):
    # arion also loads cfg separately via Nix
    # arion_cleanup(cfg, log)
    run_process(cfg, log, ['arion', 'up', '-d'])
    time.sleep(3) # TODO does this prevent "network not found" error?

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
            "--public-dir", cfg.arion.bind_mounts.public,
            "--referendum-question", cfg.election.question,
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

def vote(cfg, log, device_number, candidate, spoil=False):
    run_in_container(
        cfg, log, "device.py", "device", device_number,
        [
            "vote",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--private-dir", cfg.arion.bind_mounts.private,
            "--device-number", str(device_number),
            "--candidate", candidate,
            "--spoil", str(spoil),
        ]
    )

@explain_step
def vote_all(cfg, log):
    votes_so_far = 0

    # remember a "candidate" might also be an answer to a referendum question!
    # TODO have they come up with a better name for that in the 2.0 spec?
    for (candidate, n_votes) in cfg.votes.items():

        for _ in range(n_votes.spoil):
            # hack to iterate over devices, just to show there can be more than one
            device_number = votes_so_far % cfg.election.devices.count + 1
            vote(cfg, log, device_number, candidate, spoil=True)
            votes_so_far += 1

        for _ in range(n_votes.cast):
            device_number = votes_so_far % cfg.election.devices.count + 1
            vote(cfg, log, device_number, candidate)
            votes_so_far += 1

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

def election(cfg, log):
    build_manifest(cfg, log)
    announce_key_ceremony(cfg, log)
    key_ceremony_round1(cfg, log)
    key_ceremony_round2(cfg, log)
    key_ceremony_round3(cfg, log)
    publish_joint_key(cfg, log)
    build_election(cfg, log)
    add_devices(cfg, log)
    vote_all(cfg, log)
    tally(cfg, log)
    decrypt_shares(cfg, log)
    decrypt_results(cfg, log)
    verify(cfg, log)

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
    else:
        main(cfg, log)

@click.group(cls=DefaultGroup, default='election', default_if_no_args=True)
def cli() -> None:
    pass

cli.add_command(ElectionCommand)

if __name__ == '__main__':
    cli()
