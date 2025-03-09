#!/usr/bin/env python3

# TODO add nodes for checking all the ballots are accounted for!

import click
from typing import Any, Union, Optional, Callable, List, Dict
from collections import defaultdict
from utils import (
    # build_election,
    # load_submitted_ballots,
    # load_cast_ballots,
    # load_tally_shares,
    # load_spoiled_shares,
    # load_spoiled_results,
    # load_guardian_pubkeys_dict,
    # load_spoiled_ballots,
    # to_public_record,
    from_public_record,
    list_submitted_ballot_fmtargs,
    list_cast_ballot_fmtargs,
    list_spoiled_ballot_fmtargs,
    list_guardian_backup_fmtargs,
    list_guardian_verification_fmtargs,
)


### utils ###

# TODO hashable type for fmtargs to use in lookups
# reasonable first try: tuple(sorted(kwargs.items()))
# from https://stackoverflow.com/a/2704866

# TODO util functions to use that type easily

def verify_load(pubdir, results, artifact_name, msg=None, **fmtargs):
    "Wrap from_public_record with verification stuff"
    if artifact_name in results and fmtargs in results[artifact_name]:
        return results[artifact_name][fmtargs]
    if msg is None:
        msg = artifact_name
    try:
        artifact = from_public_record(pubdir, artifact_name, **fmtargs)
        mark_verified(results, artifact_name, artifact)
        results[artifact_name][fmtargs] = artifact
        print(f'✅ {msg}')
        return artifact
    except Exception as e:
        results[artifact_name][fmtargs] = str(e)
        print(f'❌ {msg}')


### verify a node in the dependency graph ###
#
# Each function takes the main public dir `pubdir`, the main `errors` dict, a
# list of already-verified dependency nodes `vdeps` and optional extra `kwargs`
# (for example `ballot_id`). It returns whether verification succeeded.
#
# TODO is throwing an exception also OK, or should it be cast to str?
# TODO should kwargs be passed expanded instead?
#
#############################################

def verify_manifest(results, pubdir, kwargs):
    verify_load(pubdir, results, 'manifest')

def verify_ceremony_details(results, pubdir, kwargs):
    raise NotImplementedError

def verify_one_guardian_pubkey(results, pubdir, kwargs):
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_guardian_backup(results, pubdir, kwargs):
    one_guardian_pubkey = verify_one_guardian_pubkey(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_guardian_verification(results, pubdir, kwargs):
    one_guardian_pubkey = verify_one_guardian_pubkey(results, pubdir, kwargs)
    one_guardian_backup = verify_one_guardian_backup(results, pubdir, kwargs)
    raise NotImplementedError

def verify_joint_key(results, pubdir, kwargs):
    all_guardian_pubkeys = verify_all_guardian_pubkeys(results, pubdir, kwargs)
    raise NotImplementedError

def verify_constants(results, pubdir, kwargs):
    build_election = verify_build_election(results, pubdir, kwargs)
    raise NotImplementedError

def verify_context(results, pubdir, kwargs):
    build_election = verify_build_election(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_device(results, pubdir, kwargs):
    raise NotImplementedError

def verify_one_ballot_submitted(results, pubdir, kwargs):
    one_device = verify_one_device(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_cast_notice(results, pubdir, kwargs):
    one_device = verify_one_device(results, pubdir, kwargs)
    one_ballot_submitted = verify_one_ballot_submitted(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_ballot_spoiled(results, pubdir, kwargs):
    one_device = verify_one_device(results, pubdir, kwargs)
    one_ballot_submitted = verify_one_ballot_submitted(results, pubdir, kwargs)
    raise NotImplementedError

def verify_ciphertext_tally(results, pubdir, kwargs):
    context = verify_context(results, pubdir, kwargs)
    internal_manifest = verify_internal_manifest(results, pubdir, kwargs)
    all_ballots_cast = verify_all_ballots_cast(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_tally_share(results, pubdir, kwargs):
    one_guardian_pubkey = verify_one_guardian_pubkey(results, pubdir, kwargs)
    context = verify_context(results, pubdir, kwargs)
    ciphertext_tally = verify_ciphertext_tally(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_spoiled_share(results, pubdir, kwargs):
    context = verify_context(results, pubdir, kwargs)
    one_ballot_submitted = verify_one_ballot_submitted(results, pubdir, kwargs)
    one_ballot_submitted = verify_one_ballot_submitted(results, pubdir, kwargs)
    one_ballot_spoiled = verify_one_ballot_spoiled(results, pubdir, kwargs)
    raise NotImplementedError

def verify_plaintext_tally(results, pubdir, kwargs):
    manifest = verify_manifest(results, pubdir, kwargs)
    context = verify_context(results, pubdir, kwargs)
    ciphertext_tally = verify_ciphertext_tally(results, pubdir, kwargs)
    all_tally_shares = verify_all_tally_shares(results, pubdir, kwargs)
    raise NotImplementedError

def verify_one_spoiled_result(results, pubdir, kwargs):
    manifest = verify_manifest(results, pubdir, kwargs)
    context = verify_context(results, pubdir, kwargs)
    one_ballot_spoiled = verify_one_ballot_spoiled(results, pubdir, kwargs)
    one_ballot_spoiled = verify_one_ballot_spoiled(results, pubdir, kwargs)
    one_spoiled_share = verify_one_spoiled_share(results, pubdir, kwargs)
    one_spoiled_share = verify_one_spoiled_share(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_guardian_pubkeys(results, pubdir, kwargs):
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    one_guardian_pubkey = verify_one_guardian_pubkey(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_ballots_submitted(results, pubdir, kwargs):
    one_ballot_submitted = verify_one_ballot_submitted(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_ballots_spoiled(results, pubdir, kwargs):
    one_ballot_spoiled = verify_one_ballot_spoiled(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_cast_notices(results, pubdir, kwargs):
    one_cast_notice = verify_one_cast_notice(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_spoiled_shares(results, pubdir, kwargs):
    one_spoiled_share = verify_one_spoiled_share(results, pubdir, kwargs)
    all_guardian_pubkeys = verify_all_guardian_pubkeys(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_spoiled_results(results, pubdir, kwargs):
    one_spoiled_result = verify_one_spoiled_result(results, pubdir, kwargs)
    all_guardian_pubkeys = verify_all_guardian_pubkeys(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_tally_shares(results, pubdir, kwargs):
    one_tally_share = verify_one_tally_share(results, pubdir, kwargs)
    all_guardian_pubkeys = verify_all_guardian_pubkeys(results, pubdir, kwargs)
    raise NotImplementedError

def verify_build_election(results, pubdir, kwargs):
    manifest = verify_manifest(results, pubdir, kwargs)
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    joint_key = verify_joint_key(results, pubdir, kwargs)
    raise NotImplementedError

def verify_internal_manifest(results, pubdir, kwargs):
    build_election = verify_build_election(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_guardian_backups(results, pubdir, kwargs):
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    one_guardian_backup = verify_one_guardian_backup(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_guardian_verifications(results, pubdir, kwargs):
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    one_guardian_verification = verify_one_guardian_verification(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_devices(results, pubdir, kwargs):
    one_device = verify_one_device(results, pubdir, kwargs)
    raise NotImplementedError

def verify_all_ballots_cast(results, pubdir, kwargs):
    raise NotImplementedError

def verify_gather_announce(results, pubdir, kwargs):
    manifest = verify_manifest(results, pubdir, kwargs)
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    raise NotImplementedError

def verify_gather_ceremony(results, pubdir, kwargs):
    ceremony_details = verify_ceremony_details(results, pubdir, kwargs)
    joint_key = verify_joint_key(results, pubdir, kwargs)
    all_guardian_pubkeys = verify_all_guardian_pubkeys(results, pubdir, kwargs)
    all_guardian_backups = verify_all_guardian_backups(results, pubdir, kwargs)
    all_guardian_verifications = verify_all_guardian_verifications(results, pubdir, kwargs)
    raise NotImplementedError

def verify_gather_constants(results, pubdir, kwargs):
    joint_key = verify_joint_key(results, pubdir, kwargs)
    constants = verify_constants(results, pubdir, kwargs)
    context = verify_context(results, pubdir, kwargs)
    raise NotImplementedError

def verify_gather_config(results, pubdir, kwargs):
    all_devices = verify_all_devices(results, pubdir, kwargs)
    gather_announce = verify_gather_announce(results, pubdir, kwargs)
    gather_ceremony = verify_gather_ceremony(results, pubdir, kwargs)
    gather_constants = verify_gather_constants(results, pubdir, kwargs)
    raise NotImplementedError

def verify_gather_ballots(results, pubdir, kwargs):
    all_ballots_submitted = verify_all_ballots_submitted(results, pubdir, kwargs)
    all_ballots_spoiled = verify_all_ballots_spoiled(results, pubdir, kwargs)
    all_cast_notices = verify_all_cast_notices(results, pubdir, kwargs)
    all_spoiled_results = verify_all_spoiled_results(results, pubdir, kwargs)
    raise NotImplementedError

def verify_gather_decryptions(results, pubdir, kwargs):
    plaintext_tally = verify_plaintext_tally(results, pubdir, kwargs)
    all_spoiled_results = verify_all_spoiled_results(results, pubdir, kwargs)
    raise NotImplementedError

def verify_gather_election(results, pubdir, kwargs):
    gather_config = verify_gather_config(results, pubdir, kwargs)
    gather_ballots = verify_gather_ballots(results, pubdir, kwargs)
    gather_decryptions = verify_gather_decryptions(results, pubdir, kwargs)
    raise NotImplementedError


### cli ###

def main(pubdir, verifier_id):

    # main state is a dict of artifact_name -> fmtargs -> either str or result
    # it accumulates both successful result objects and error messages
    # TODO explicit typing for the error message strs?
    results = defaultdict(lambda: {})

    print('verifying public election artifacts...\n')
    verify_manifest(results, pubdir, {})

    # TODO summary here


@click.command("verify")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--verifier-id",
    prompt="Unique ID for this verifier",
    help="Used when saving the final JSON summary file",
    type=click.STRING,
)
def VerifyCommand(
    public_dir: str,
    verifier_id: str,
) -> None:
    """Verify all public election artifacts.
    """
    # TODO parse and pass cfg here
    main(public_dir, verifier_id)

@click.group
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()

