#!/usr/bin/env python3

import click
import json
import subprocess

from click_default_group import DefaultGroup
from dotmap import DotMap
from os import makedirs
from os.path import join, exists
from pprint import pprint
from pygments import highlight, lexers, formatters
from typing import Optional


# see logs.py for electionguard's separate LOG
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s\n')
LOG = logging.getLogger('electionguard-cardano')


### utilities ###

def print_colorful_json(msg):
	# based on https://stackoverflow.com/a/32166163
	msg = msg.replace("'", '"')
	formatted_json = json.dumps(json.loads(msg), indent=2)
	colorful_json = highlight(
		formatted_json,
		lexers.JsonLexer(),
		formatters.TerminalFormatter()
	)
	print(colorful_json)

def parse_config(cfg_path, pause_to_explain):
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
    cfg.pause_to_explain = pause_to_explain
    cfg.votes = dict(cfg.votes) # TODO is this the simplest way to enable iteration?
    ecfg = cfg.election
    ecfg.guardians.sequence_order = [*range(1, ecfg.guardians.count + 1)]
    ecfg.guardians.ids = [f"guardian_{i}" for i in ecfg.guardians.sequence_order]
    return cfg

def run_in_container(cfg, mode, container_number, args, **kwargs):
    container_name = cfg.arion.project_name + "-" + mode + str(container_number) + "-1"
    script_path = join(cfg.arion.bind_mounts.scripts, mode + '.py')
    # TODO python don't write bytecode (here or in the image?)
    args = ["docker", "exec", container_name,
            "poetry", "run", script_path] + args
    kwargs.update(stdout=subprocess.PIPE, text=True)
    LOG.info(' '.join(args))
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    # expects scripts to print a json dump of some info
    # for example: print(json.dumps(locals()))
    # TODO not useful long term?
    try:
        stdout = stdout.strip()
        if len(stdout) > 0:
            print_colorful_json(stdout)
        if stderr is not None:
            stderr = stderr.strip()
            if len(stderr) > 0:
                print(stderr)
    except json.decoder.JSONDecodeError:
        msg = stdout
        if stderr is not None:
            msg += '\n' + stderr
        LOG.error(msg)

def explain_step(fn):
    def decorated_fn(cfg, *args, **kwargs):
        header = f'### {fn.__name__} ###'
        print('\n' + header)
        if cfg.pause_to_explain:
            print('#  ')
            while True:
                if len(input('#  ').strip()) == 0:
                    print('#' * len(header) + '\n')
                    break
        else:
            print()
        return fn(cfg, *args, **kwargs)
    return decorated_fn

def run_single_step(cfg, fn_name):
    fn = globals()[fn_name]
    fn(cfg)

def arion_cleanup(cfg):
    # in case a previous run failed
    # TODO can Docker or Arion do this rm step more safely?
    subprocess.check_call(['arion', 'down'])
    data_dir = './data'
    if exists(data_dir):
        subprocess.check_call(['sudo', 'rm', '-rf', data_dir])

@explain_step
def setup(cfg):
    # arion also loads cfg separately via Nix
    arion_cleanup(cfg)
    subprocess.check_call(['arion', 'up', '-d'])

@explain_step
def teardown(cfg):
    subprocess.check_call(['arion', 'down'])


### election ###

@explain_step
def build_manifest(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "build-manifest",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--referendum-question", cfg.election.question,
        ]
    )

@explain_step
def announce_key_ceremony(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "announce-key-ceremony",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--guardian-count", str(cfg.election.guardians.count),
            "--guardian-quorum", str(cfg.election.guardians.quorum),
        ]
    )

def key_ceremony_round(cfg, ceremony_round):
    for guardian_id, sequence_order in \
            zip(cfg.election.guardians.ids, cfg.election.guardians.sequence_order):
        run_in_container(
            cfg, "guardian", sequence_order,
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
def key_ceremony_round1(cfg):
    key_ceremony_round(cfg, 1)


@explain_step
def key_ceremony_round2(cfg):
    key_ceremony_round(cfg, 2)

@explain_step
def key_ceremony_round3(cfg):
    key_ceremony_round(cfg, 3)

@explain_step
def publish_joint_key(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "publish-joint-key",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

@explain_step
def build_election(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "build-election",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

def add_device(cfg, device_number):
    run_in_container(
        cfg, "device", device_number,
        [
            "add-device",
            "--public-dir", cfg.arion.bind_mounts.public,
            "--device-number", str(device_number),
        ]
    )

@explain_step
def add_devices(cfg):
    for n in range(1, cfg.election.devices.count + 1):
        add_device(cfg, n)

def vote(cfg, device_number, candidate, spoil=False):
    run_in_container(
        cfg, "device", device_number,
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
def vote_all(cfg):
    votes_so_far = 0

    # remember a "candidate" might also be an answer to a referendum question!
    # TODO have they come up with a better name for that in the 2.0 spec?
    for (candidate, n_votes) in cfg.votes.items():

        for _ in range(n_votes.spoil):
            # hack to iterate over devices, just to show there can be more than one
            device_number = votes_so_far % cfg.election.devices.count + 1
            vote(cfg, device_number, candidate, spoil=True)
            votes_so_far += 1

        for _ in range(n_votes.cast):
            device_number = votes_so_far % cfg.election.devices.count + 1
            vote(cfg, device_number, candidate)
            votes_so_far += 1

@explain_step
def tally(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "tally",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

@explain_step
def decrypt_shares(cfg):
    for guardian_id, sequence_order in \
            zip(cfg.election.guardians.ids, cfg.election.guardians.sequence_order):
        run_in_container(
            cfg, "guardian", sequence_order,
            [
                "decrypt-shares",
                "--public-dir", cfg.arion.bind_mounts.public,
                "--private-dir", cfg.arion.bind_mounts.private,
                "--guardian-id", guardian_id,
            ]
        )

@explain_step
def decrypt_results(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "decrypt-results",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

@explain_step
def summary(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "summary",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )

def election(cfg):
    build_manifest(cfg)
    announce_key_ceremony(cfg)
    key_ceremony_round1(cfg)
    key_ceremony_round2(cfg)
    key_ceremony_round3(cfg)
    publish_joint_key(cfg)
    build_election(cfg)
    add_devices(cfg)
    vote_all(cfg)
    tally(cfg)
    decrypt_shares(cfg)
    decrypt_results(cfg)
    summary(cfg)


### cli ###

@click.command("election")
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
def ElectionCommand(
    pause_to_explain: bool,
    single_step: Optional[str]
) -> None:
    """Run an election with some options in a JSON config file.
    """
    cfg = parse_config('election.json', pause_to_explain)
    if single_step:
        run_single_step(cfg, single_step)
    else:
        try:
            setup(cfg) # TODO down and up again if needed?
            election(cfg)
        except Exception as e:
            pprint(e) # TODO recover?
            LOG.error('Election failed :(')
        finally:
            teardown(cfg)

@click.group(cls=DefaultGroup, default='election', default_if_no_args=True)
def cli() -> None:
    pass

cli.add_command(ElectionCommand)

if __name__ == '__main__':
    cli()
