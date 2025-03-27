#!/usr/bin/env python3

import os
import click
import logging
import random
from typing import Optional
from utils import (
    init_log,
    public_path,
    list_submitted_ballot_fmtargs,
    list_cast_ballot_fmtargs,
    list_spoiled_ballot_fmtargs,
    list_ballot_ids,
)


### utilities ###

def list_own_ballot_fmtargs(privdir):
    "List fmtargs only of ballots created by this device"
    bdir = os.path.join(privdir, 'plaintext_ballots')
    try:
        return [{'ballot_id': i} for i in list_ballot_ids(bdir)]
    except FileNotFoundError as e:
        log.error(e)
        return []


### attacks ###
#
# See also ATTACKS in config.py for info about how to run them

def admin_withhold_manifest(log, pubdir, privdir, step):
    "A silly attack that's fast to debug because it targets the first step."
    log.info(f'running during {step} step')
    manifest_path = public_path(pubdir, 'manifest')
    log.info(f'removing {manifest_path}')
    try:
        os.remove(manifest_path)
        log.info('attack finished')
    except Exception as e:
        log.error(e)

def device_withhold_submitted_ballot(log, pubdir, privdir, step):
    """Prevent a ballot from being initially submitted. This would be caught in
    the current ElectionGuard setup by a voter checking the official website
    after they finish voting, or in the ideal blockchain setup by checking the
    mempool/recent transactions before saying whether to cast or spoil it.
    """
    log.info(f'running during {step} step')
    try:
        ballot_fmtargs = random.choice(list_own_ballot_fmtargs(privdir))
    except IndexError:
        log.error('no ballots submitted. abort attack')
        return
    ballot_path = public_path(pubdir, 'ballot_submitted', **ballot_fmtargs)
    log.info(f'removing {ballot_path}')
    try:
        os.remove(ballot_path)
        log.info('attack finished')
    except Exception as e:
        log.error(e)

def device_withhold_cast_ballot(log, pubdir, privdir, step):
    """Prevent a cast notice from being published. This would make it appear
    that the voter never said whether to cast or spoil, but is targeted to the
    case when they actually cast. They would notice if they tried to look up
    the cast vote on the website or blockchain after voting. This attack could
    be made impossible by doing the cast/spoil step from a phone, at the cost
    of potentially linking the voter's identity to the cast ballot.
    """
    log.info(f'running during {step} step')
    own_ballots   = set(d['ballot_id'] for d in list_own_ballot_fmtargs(privdir))
    cast_ballots  = set(d['ballot_id'] for d in list_cast_ballot_fmtargs(pubdir))
    valid_choices = [{'ballot_id': i} for i in own_ballots.intersection(cast_ballots)]
    try:
        ballot_fmtargs = random.choice(valid_choices)
    except IndexError:
        log.error('abort because this device has no cast ballots to withhold')
        return
    ballot_path = public_path(pubdir, 'cast_notice', **ballot_fmtargs)
    log.info(f'removing {ballot_path}')
    try:
        os.remove(ballot_path)
        log.info('attack finished')
    except Exception as e:
        log.error(e)

def device_withhold_spoiled_ballot(log, pubdir, privdir, step):
    """Prevent a spoiled ballot from being published. This would make it appear
    that the voter never said whether to cast or spoil, but is targeted to the
    case when they actually spoiled. They would notice if they tried to look up
    the spoiled vote on the website or blockchain after voting. This attack could
    be made impossible by doing the cast/spoil step from a phone, at the cost
    of potentially linking the voter's identity to the spoiled ballot.
    """
    log.info(f'running during {step} step')
    own_ballots     = set(d['ballot_id'] for d in list_own_ballot_fmtargs(privdir))
    spoiled_ballots = set(d['ballot_id'] for d in list_spoiled_ballot_fmtargs(pubdir))
    valid_choices   = [{'ballot_id': i} for i in own_ballots.intersection(spoiled_ballots)]
    try:
        ballot_fmtargs = random.choice(valid_choices)
    except IndexError:
        log.error('abort because this device has no spoiled ballots to withhold')
        return
    ballot_path = public_path(pubdir, 'ballot_spoiled', **ballot_fmtargs)
    log.info(f'removing {ballot_path}')
    try:
        os.remove(ballot_path)
        log.info('attack finished')
    except Exception as e:
        log.error(e)

def admin_ghost_after_vote(log, pubdir, privdir, step):
    """This simulates the election authority becoming non-cooperative after
    they see that the voting is going in a direction they don't like. (There's
    no defense against them quitting earlier during the setup phase, and no
    obvious reason why they would want to) Currently, this attack will cause
    the election to fail. But it would be fairly simple to amend the protocol
    to say that others can step in and perform any result-tallying step if the
    admin doesn't do it within the expected time window. The admin doesn't have
    any private information. Going even further, all the tally steps could be
    carried out by other participants and the admin could be relegated to only
    controlling the setup.
    """

    log.info(f'running during {step} step')

    if step == 'tally':
        tally_path = public_path(pubdir, 'ciphertext_tally')
        log.info(f'removing {tally_path}')
        try:
            os.remove(tally_path)
        except Exception as e:
            log.error(e)

    elif step == 'decrypt_results':
        ballot_fmtargs = list_spoiled_ballot_fmtargs(pubdir)
        for fmtargs in ballot_fmtargs:
            ballot_path = public_path(pubdir, 'spoiled_result', **fmtargs)
            log.info(f'removing {ballot_path}')
            try:
                os.remove(ballot_path)
            except Exception as e:
                log.error(e)
        log.info('attack finished')

    else:
        raise Exception(f'unexpected step {step}')
    log.info('')


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
