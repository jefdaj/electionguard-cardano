#!/usr/bin/env python3

import subprocess
import json
import click

from os import makedirs
from os.path import join
from pprint import pprint
from dotmap import DotMap
from pygments import highlight, lexers, formatters


# NOTE see logs.py for electionguard's separate LOG
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s\n%(message)s\n')
LOG = logging.getLogger('electionguard-cardano')


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


# TODO write this as a decorator so it can print the name of the step too?
def explain(cfg):
    if cfg.pause_to_explain:
        print()
        while True:
            msg = input('# ')
            if len(msg) == 0:
                break


def arion_up(cfg):
    # NOTE arion also loads cfg separately via Nix
    explain(cfg)
    subprocess.check_call(['arion', 'up', '-d'])


def arion_down(cfg):
    explain(cfg)
    subprocess.check_call(['arion', 'down'])


def run_in_container(cfg, mode, container_number, args, **kwargs):
    # TODO document this
    container_name = cfg.project_name + "-" + mode + str(container_number) + "-1"
    script_path = join(cfg.bind_mounts.scripts, mode + '.py')
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


def build_manifest(cfg):
    # uncomment for interactive script:
    # question = input('Referendum-style question to be asked: ')
    explain(cfg)
    question = 'Are pineapples still cool?'
    run_in_container(
        cfg, "admin", 1,
        [
            "build-manifest",
            "--public-records-dir", cfg.bind_mounts.public,
            "--referendum-question", question,
        ]
    )


def announce_key_ceremony(cfg):
    # TODO remove this step?
    explain(cfg)
    run_in_container(
        cfg, "admin", 1,
        [
            "announce-key-ceremony",
            "--guardian-count"    , str(cfg.guardians.count),
            "--quorum"            , str(cfg.guardians.quorum),
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )


def key_ceremony_round(cfg, current_round):
    explain(cfg)
    for guardian_id, sequence_order in zip(cfg.guardians.ids, cfg.guardians.sequence_order):
        run_in_container(
            cfg, "guardian", sequence_order,
            [
                "key-ceremony",
                "--guardian-count"         , str(cfg.guardians.count),
                "--quorum"                 , str(cfg.guardians.quorum),
                "--public-records-dir"     , cfg.bind_mounts.public,
                "--private-records-dir"    , cfg.bind_mounts.private,
                "--guardian-id"            , guardian_id,
                "--guardian-sequence-order", str(sequence_order),
                "--current-round"          , str(current_round),
            ]
        )


def publish_joint_key(cfg):
    explain(cfg)
    run_in_container(
        cfg, "admin", 1,
        [
            "publish-joint-key",
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )


def build_election(cfg):
    explain(cfg)
    run_in_container(
        cfg, "admin", 1,
        [
            "build-election",
            "--guardian-count"    , str(cfg.guardians.count),
            "--quorum"           , str(cfg.guardians.quorum),
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )


def add_device(cfg, device_number):
    explain(cfg)
    run_in_container(
        cfg, "device", device_number,
        [
            "add-device",
            "--device-number"     , str(device_number),
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )


def vote(cfg, candidate_id, spoil=False):
    run_in_container(
        cfg, "device", 1, # TODO code for other devices?
        [
            "vote",
            "--guardian-count"     , str(cfg.guardians.count),
            "--quorum"             , str(cfg.guardians.quorum),
            "--public-records-dir" , cfg.bind_mounts.public,
            "--private-records-dir", cfg.bind_mounts.private,
            "--candidate-id"       , candidate_id,
            "--spoil"              , str(spoil),
        ]
    )


def vote_all(cfg):
    explain(cfg)
    vote(cfg, candidate_id="referendum-question-affirmative-selection")
    vote(cfg, candidate_id="referendum-question-negative-selection")
    vote(cfg, candidate_id="referendum-question-affirmative-selection")
    vote(cfg, candidate_id="referendum-question-affirmative-selection", spoil=True)
    vote(cfg, candidate_id="referendum-question-negative-selection"   , spoil=True)


def tally(cfg):
    explain(cfg)
    run_in_container(
        cfg, "admin", 1,
        [
            "tally",
            "--guardian-count"     , str(cfg.guardians.count),
            "--quorum"             , str(cfg.guardians.quorum),
            "--public-records-dir" , cfg.bind_mounts.public,
        ]
    )


def decrypt_shares(cfg):
    explain(cfg)
    for guardian_id, sequence_order in zip(cfg.guardians.ids, cfg.guardians.sequence_order):
        run_in_container(
            cfg, "guardian", sequence_order,
            [
                "decrypt-share",
                "--guardian-count"         , str(cfg.guardians.count),
                "--quorum"                 , str(cfg.guardians.quorum),
                "--public-records-dir"     , cfg.bind_mounts.public,
                "--private-records-dir"    , cfg.bind_mounts.private,
                "--guardian-id"            , guardian_id,
                "--guardian-sequence-order", str(sequence_order),
            ]
        )


def parse_config(cfg_path, pause_to_explain):
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
    cfg.pause_to_explain = pause_to_explain
    cfg.guardians.sequence_order = [*range(1, cfg.guardians.count + 1)]
    cfg.guardians.ids = [f"guardian_{i}" for i in cfg.guardians.sequence_order]
    return cfg


def election(cfg):
    arion_up(cfg) # TODO down and up again if needed?
    build_manifest(cfg)
    announce_key_ceremony(cfg)
    key_ceremony_round(cfg, 1)
    key_ceremony_round(cfg, 2)
    key_ceremony_round(cfg, 3)
    # TODO should there be a "publish final guardian records" step here?
    publish_joint_key(cfg)
    build_election(cfg)
    for n in range(1, cfg.votingDevices.count + 1):
        add_device(cfg, n)
    vote_all(cfg)
    tally(cfg)
    # decrypt_shares(cfg)
    # decrypt_combine()
    arion_down(cfg)


@click.command("election")
@click.option(
    "--pause-to-explain",
    prompt="Pause so you can explain before each step?",
    help="Pauses the script while you type something before each step.",
    type=click.BOOL,
    # TODO default to false
)
def ElectionCommand(
    pause_to_explain: bool
) -> None:
    """Run an election with some options in a JSON config file.
    """
    cfg = parse_config('election.json', pause_to_explain)
    election(cfg)


@click.group()
def cli() -> None:
    pass

cli.add_command(ElectionCommand)

if __name__ == '__main__':
    cli()
