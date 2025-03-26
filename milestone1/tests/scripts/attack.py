#!/usr/bin/env python3

import os
import click
import logging
import random
from typing import Optional
from utils import (
    init_log,
    public_path,
)


### attacks ###
#
# See also ATTACKS in config.py for info about how to run them

def withhold_manifest(log, pubdir, privdir, step):
    "A pointless attack that's fast to debug because it targets the first step."
    manifest_path = public_path(pubdir, 'manifest')
    log.info(f'removing {manifest_path}')
    try:
        os.remove(manifest_path)
    except Exception as e:
        log.error(e)

# def withhold_submitted_ballot(log, pubdir, privdir, step):
#     raise NotImplementedError

# def withhold_cast_ballot(log, pubdir, privdir, step):
#     raise NotImplementedError

# def withhold_spoiled_ballot(log, pubdir, privdir, step):
#     raise NotImplementedError


### main ###

def main(log, public_dir, private_dir, fn_name, step, random_seed):
    random.seed(random_seed) # TODO do within each fn, or just here?
    try:
        attack_fn = globals()[fn_name]
    except KeyError:
        log.error('no such attack fn: {fn_name}')
        raise
    attack_fn(log, public_dir, private_dir, step)


### cli ###

@click.command("attack")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--private-dir",
    prompt="Private records directory",
    help="The location of a directory into which will be placed the guardian's private keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--logfile",
    prompt="Logfile (default: stdout)",
    help="Where to log printed messages",
    type=click.STRING,
)
@click.option(
    "--attack-fn",
    prompt="Attack function name",
    help="Which attack to run",
    type=click.STRING,
)
@click.option(
    "--step",
    prompt="Election step",
    help="Which step of the election is currently going on",
    type=click.STRING,
)
@click.option(
    "--random-seed",
    prompt="Random seed",
    help="Used when picking files to edit",
    type=click.INT,
)
def AttackCommand(
    public_dir: str,
    private_dir: str,
    attack_fn: str,
    step: str,
    random_seed: int,
    logfile: Optional[str],
) -> None:
    # TODO parse and pass cfg here?
    log = init_log(logfile, logging.INFO)
    main(log, public_dir, private_dir, attack_fn, step, random_seed)

@click.group
def cli() -> None:
    pass

cli.add_command(AttackCommand)

if __name__ == '__main__':
    cli()
