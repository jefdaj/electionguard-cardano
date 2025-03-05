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

def parse_config(cfg_path):
    with open(cfg_path, 'r') as f:
        js = json.load(f)
    cfg = DotMap(js)
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

def setup(cfg):
    # arion also loads cfg separately via Nix
    subprocess.check_call(['arion', 'up', '-d'])

def teardown(cfg):
    subprocess.check_call(['arion', 'down'])


### verify ###

def verify(cfg):
    print('verify would go here')
    raise SystemExit
    run_in_container(
        cfg, "verifier", 1,
        [
            "verify",
            "--public-dir", cfg.arion.bind_mounts.public,
        ]
    )


### cli ###

@click.command("verify")
def VerifyCommand(
) -> None:
    """Verify all public election artifacts.
    """
    cfg = parse_config('verify.json')
    try:
        setup(cfg)
        verify(cfg)
    except Exception as e:
        pprint(e)
        LOG.error('Election failed :(')
    finally:
        teardown(cfg)

@click.group(cls=DefaultGroup, default='verify', default_if_no_args=True)
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()
