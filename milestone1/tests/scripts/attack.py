#!/usr/bin/env python3

import json
import os
import click
import logging
import random
from typing import Optional, List
from utils import (
    init_log,
    public_path,
    list_submitted_ballot_fmtargs,
    list_cast_ballot_fmtargs,
    list_spoiled_ballot_fmtargs,
    list_ballot_ids,
    from_private_record,
)
import re
import string
from electionguard.key_ceremony import ElectionKeyPair

# from pprint import pprint

### utilities ###

HEX_CHARS = string.digits + string.ascii_uppercase[:6]

def mutate_hex_string(log: logging.Logger, hex_str: str) -> str:
    "Randomly change one char in a hex string"
    new_str_chars = list(hex_str)
    i = random.randint(0, len(hex_str)-1)
    old_char = hex_str[i]
    new_char = None
    while new_char is None or new_char == old_char:
        new_char = random.choice(HEX_CHARS)
    new_str_chars[i] = new_char
    new_hex_str = ''.join(new_str_chars)
    log.info(f'mutated char {i}: {old_char} -> {new_char}')
    log.info(f'old: {hex_str}')
    log.info(f'new: {new_hex_str}')
    return new_hex_str

def json_edit_matching_values(root, keys_to_match, value_edit_fn):
    """For each (key,value) pair nested in the root JSON dict,
    apply value_edit_fn to the pair if the key is in the list.
    Note that value_edit_fn takes the key and value, but only returns
    a new value; the key is mainly for logging.
    """
    if isinstance(root, dict):
        for (k, v) in root.items():
            if k in keys_to_match:
                root[k] = value_edit_fn(k, v)
            json_edit_matching_values(v, keys_to_match, value_edit_fn)
    elif isinstance(root, list):
        for v in root:
            json_edit_matching_values(v, keys_to_match, value_edit_fn)

def edit_random_matching_crypto_value_in_place(
    log: logging.Logger,
    json_path: str,
    keys: List[str],
):
    with open(json_path, 'r') as f:
        json_dict = json.load(f)

    # read once just to count matching keys,
    # not editing anything
    n_matching_keys = 0
    def count_matches(k, v):
        nonlocal n_matching_keys
        n_matching_keys += 1
        return v
    json_edit_matching_values(json_dict, keys, count_matches)
    log.info(f'there are {n_matching_keys} matching keys')
    if n_matching_keys == 0:
        log.error('abort because no matching keys') # TODO raise exception and catch above instead?
        return

    # now do the actual edit
    edit_index = random.randint(0, n_matching_keys-1)
    n = 0
    def edit_chosen_match(k, v):
        nonlocal n
        if n == edit_index:
            log.info(f'targeting match {n}, {k}')
            if v is None:
                raise Exception(f'abort because {k} is None') # TODO log error instead?
            try:
                v = mutate_hex_string(log, v)
            except Exception as e:
                print(e)
        n += 1
        return v
    json_edit_matching_values(json_dict, keys, edit_chosen_match)

    # overwrite original file
    with open(json_path, 'w') as f:
        json.dump(json_dict, f)
    log.info(f'overwrote {json_path}')

def mutate_public_record_crypto_in_place(
    log: logging.Logger,
    pubdir: str,
    record_type: str,
    keys: List[str],
    **fmtargs
):
    json_path = public_path(pubdir, record_type, **fmtargs)
    log.info(f'targeting {json_path}')
    edit_random_matching_crypto_value_in_place(log, json_path, keys)

def announce_attack(fn):
    def decorated_fn(log, *args, **kwargs):
        header = f'### running {fn.__name__} ###\n'
        log.info(header)
        try:
            result = fn(log, *args, **kwargs)
            log.info(f'\n### finished {fn.__name__} ###\n')
            return result
        except Exception as e:
            log.error(f'ERROR: {e}')
            raise
    return decorated_fn

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

# TODO put back? short-circuits most of the election
@announce_attack
def admin_withhold_manifest(log, pubdir, privdir, step):
    "A silly attack that's fast to debug because it targets the first step."
    log.info(f'running during {step} step')
    manifest_path = public_path(pubdir, 'manifest')
    log.info(f'removing {manifest_path}')
    os.remove(manifest_path)

# TODO should the protocol be expected to catch this? it doesn't so far
def admin_mutate_constants(log, pubdir, privdir, step):
    log.info(f'running during {step} step')
    mutate_public_record_crypto_in_place(
        log, pubdir, 'constants',
        [
            'large_prime',
            'small_prime',
            'cofactor',
            'generator'
        ]
    )

@announce_attack
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
    os.remove(ballot_path)

@announce_attack
def device_mutate_submitted_ballot(log, pubdir, privdir, step):
    submitted_ballots = set(d['ballot_id'] for d in list_submitted_ballot_fmtargs(pubdir))
    own_ballots       = set(d['ballot_id'] for d in list_own_ballot_fmtargs(privdir))
    valid_choices = [{'ballot_id': i} for i in own_ballots.intersection(submitted_ballots)]
    ballot_fmtargs = random.choice(valid_choices)
    mutate_public_record_crypto_in_place(
        log, pubdir, 'ballot_submitted',
        [
            # 'description_hash',
            # 'manifest_hash',
            # 'pad',
            'challenge',
            'crypto_hash',
            'data'
            'proof_one_data',
            'proof_one_pad',
            'proof_one_response',
            'proof_zero_data',
            'proof_zero_pad',
            'proof_zero_response',
        ],
        **ballot_fmtargs
    )

@announce_attack
def device_mutate_spoiled_ballot(log, pubdir, privdir, step):
    spoiled_ballots = set(d['ballot_id'] for d in list_spoiled_ballot_fmtargs(pubdir))
    own_ballots     = set(d['ballot_id'] for d in list_own_ballot_fmtargs(privdir))
    valid_choices = [{'ballot_id': i} for i in own_ballots.intersection(spoiled_ballots)]
    try:
        ballot_fmtargs = random.choice(valid_choices)
    except IndexError:
        raise Exception('abort because this device has no spoiled ballots')
    mutate_public_record_crypto_in_place(
        log, pubdir, 'ballot_spoiled',
        [
            # 'description_hash',
            # 'manifest_hash',

            # I don't believe this version of ElectionGuard handles letting
            # voters decrypt their ballots using the nonce, but I may want to
            # write something covering that temporarily because it's a cool
            # feature. If so, this will become testable:
            # 'nonce',

            # 'pad',
            # 'code_seed',
            'challenge',
            'crypto_hash',
            'data'
            'proof_one_data',
            'proof_one_pad',
            'proof_one_response',
            'proof_zero_data',
            'proof_zero_pad',
            'proof_zero_response',
        ],
        **ballot_fmtargs
    )


@announce_attack
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
    os.remove(ballot_path)

@announce_attack
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
    os.remove(ballot_path)

@announce_attack
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

    # TODO is there a better way to design this so it doesn't require two steps?
    #      or is that an accurate description of admin not being there for either?

    if step == 'tally':
        tally_path = public_path(pubdir, 'ciphertext_tally')
        log.info(f'removing {tally_path}')
        os.remove(tally_path)

    elif step == 'decrypt_results':
        ballot_fmtargs = list_spoiled_ballot_fmtargs(pubdir)
        for fmtargs in ballot_fmtargs:
            ballot_path = public_path(pubdir, 'spoiled_result', **fmtargs)
            log.info(f'removing {ballot_path}')
            os.remove(ballot_path)

    else:
        raise Exception(f'unexpected step {step}')

@announce_attack
def guardian_withhold_tally_share(log, pubdir, privdir, step):
    """Simulates one of the guardians refusing to decrypt their share of the
    tally. This is a realistic possibility if the guardian is a partisan upset
    at how the election seems to be going. In the full protocol there's a
    mechanism for recovering from it using the guardian backups, but I haven't
    implemented it because the ElectionGuard authors also didn't implement it.
    Doesn't seem important for the demo anyway. So for now, we just let the
    election fail.
    """
    own_key_pair: ElectionKeyPair = from_private_record(privdir, 'election_key_pair')
    fmtargs = {'guardian_id': own_key_pair.owner_id}
    json_path = public_path(pubdir, 'tally_share', **fmtargs)
    log.info(f'removing {json_path}')
    os.remove(json_path)

@announce_attack
def guardian_withhold_spoiled_share(log, pubdir, privdir, step):
    """Simulates one of the guardians refusing to decrypt their share of an
    an individual ballot.
    """

    # find our guardian_id
    own_key_pair: ElectionKeyPair = from_private_record(privdir, 'election_key_pair')
    fmtargs = {'guardian_id': own_key_pair.owner_id}

    # choose a spoiled ballot to mess up
    try:
        ballot_fmtargs = random.choice(list_spoiled_ballot_fmtargs(pubdir))
    except IndexError:
        raise Exception('abort because there are no spoiled ballots')

    # have ballot_id and guardian_id now
    # fmtargs.update(ballot_fmtargs)
    # TODO name it ballot_id here too?
    fmtargs['spoiled_id'] = ballot_fmtargs['ballot_id']

    json_path = public_path(pubdir, 'spoiled_share', **fmtargs)
    log.info(f'removing {json_path}')
    os.remove(json_path)


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
    # log.info(f'running an attack with locals: {locals()}')
    main(log, public_dir, private_dir, attack_fn, step, random_seed)

@click.group
def cli() -> None:
    pass

cli.add_command(AttackCommand)

if __name__ == '__main__':
    cli()
