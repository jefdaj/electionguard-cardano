#!/usr/bin/env python3

import click
import json
import subprocess

from click_default_group import DefaultGroup
from dotmap import DotMap
from os import makedirs
from os.path import join
from shutil import rmtree
from pprint import pprint
from pygments import highlight, lexers, formatters

# see logs.py for electionguard's separate LOG
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s\n%(message)s\n')
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
    cfg.guardians.sequence_order = [*range(1, cfg.guardians.count + 1)]
    cfg.guardians.ids = [f"guardian_{i}" for i in cfg.guardians.sequence_order]
    return cfg

def run_in_container(cfg, mode, container_number, args, **kwargs):
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

def arion_cleanup(cfg):
    # in case a previous run failed
    # TODO can the rm be safer?
    subprocess.check_call(['arion', 'down'])
    rmtree('./data', ignore_errors=True)

@explain_step
def arion_up(cfg):
    # arion also loads cfg separately via Nix
    # arion_cleanup(cfg)
    subprocess.check_call(['arion', 'up', '-d'])

@explain_step
def arion_down(cfg):
    subprocess.check_call(['arion', 'down'])


### election ###

@explain_step
def build_manifest(cfg):
    # uncomment for interactive script:
    # question = input('Referendum-style question to be asked: ')
    question = 'Are pineapples still cool?'
    run_in_container(
        cfg, "admin", 1,
        [
            "build-manifest",
            "--public-records-dir", cfg.bind_mounts.public,
            "--referendum-question", question,
        ]
    )

@explain_step
def announce_key_ceremony(cfg):
    # TODO rethink where this step fits?
    run_in_container(
        cfg, "admin", 1,
        [
            "announce-key-ceremony",
            "--guardian-count"    , str(cfg.guardians.count),
            "--quorum"            , str(cfg.guardians.quorum),
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )

@explain_step
def key_ceremony_round(cfg, current_round):
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

@explain_step
def publish_joint_key(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "publish-joint-key",
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )

@explain_step
def build_election(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "build-election",
            "--guardian-count"    , str(cfg.guardians.count),
            "--quorum"           , str(cfg.guardians.quorum),
            "--public-records-dir", cfg.bind_mounts.public,
        ]
    )

@explain_step
def add_device(cfg, device_number):
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

# TODO split into sections so the cast and spoil can be explained separately?
@explain_step
def vote_all(cfg):
    vote(cfg, candidate_id="referendum-question-affirmative-selection")
    vote(cfg, candidate_id="referendum-question-negative-selection")
    vote(cfg, candidate_id="referendum-question-affirmative-selection")
    vote(cfg, candidate_id="referendum-question-affirmative-selection", spoil=True)
    vote(cfg, candidate_id="referendum-question-negative-selection"   , spoil=True)

@explain_step
def tally(cfg):
    run_in_container(
        cfg, "admin", 1,
        [
            "tally",
            "--guardian-count"     , str(cfg.guardians.count),
            "--quorum"             , str(cfg.guardians.quorum),
            "--public-records-dir" , cfg.bind_mounts.public,
        ]
    )

@explain_step
def decrypt_shares(cfg):
    for guardian_id, sequence_order in zip(cfg.guardians.ids, cfg.guardians.sequence_order):
        run_in_container(
            cfg, "guardian", sequence_order,
            [
                "decrypt-shares",
                "--public-records-dir"     , cfg.bind_mounts.public,
                "--private-records-dir"    , cfg.bind_mounts.private,
                "--guardian-id"            , guardian_id,
            ]
        )

def election(cfg):
    # build_manifest(cfg)
    # announce_key_ceremony(cfg)
    # for n in range(1, 4):
    #     key_ceremony_round(cfg, n)
    # # TODO should there be a "publish final guardian records" step here?
    # publish_joint_key(cfg)
    # build_election(cfg)
    # for n in range(1, cfg.votingDevices.count + 1):
    #     add_device(cfg, n)
    # vote_all(cfg)
    # tally(cfg)
    decrypt_shares(cfg)
    # decrypt_combine()


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
def ElectionCommand(
    pause_to_explain: bool
) -> None:
    """Run an election with some options in a JSON config file.
    """
    cfg = parse_config('election.json', pause_to_explain)
    try:
        arion_up(cfg) # TODO down and up again if needed?
        election(cfg)
    except Exception as e:
        pprint(e) # TODO recover?
    finally:
        arion_down(cfg)

@click.group(cls=DefaultGroup, default='election', default_if_no_args=True)
def cli() -> None:
    pass

cli.add_command(ElectionCommand)

if __name__ == '__main__':
    cli()
