#!/usr/bin/env python3

# TODO add nodes for checking all the ballots are accounted for!

import click
from typing import Any, Union, Optional, Callable, List, Dict, Tuple
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
    # list_submitted_ballot_fmtargs,
    # list_cast_ballot_fmtargs,
    # list_spoiled_ballot_fmtargs,
    # list_guardian_backup_fmtargs,
    # list_guardian_verification_fmtargs,
    from_public_record,
    CaptureLog,
)
import logging
from pprint import pprint

from electionguard.manifest import Manifest
from electionguard.key_ceremony import (
    CeremonyDetails,
    # ElectionJointKey,
    # ElectionKeyPair,
    ElectionPublicKey,
    # ElectionPartialKeyBackup,
    # ElectionPartialKeyVerification,
    # combine_election_public_keys,
    # generate_election_key_pair,
    # generate_election_partial_key_backup,
    # verify_election_partial_key_backup
)


### utils ###

# TODO util functions to use that type easily

# normally one of the keys in the PUBLIC_RECORDS map,
# but might also be prefixed with one_, all_, gather_, etc.
TargetName = str

# any extra arguments needed to identify a record (guardian_id etc)
# has to be frozen (hashable) to go in results below
RecordArgs = Tuple[Tuple[str, Any]]

# from https://stackoverflow.com/a/2704866
def freeze_kwargs(kwargs):
    return tuple(sorted(kwargs.items()))

# error message
Failure = str

# successfully verified public record
Success = Any

# main state of the verify program
ResultsCache = Dict[TargetName, Dict[RecordArgs, Union[Failure, Success]]]


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

def verify_manifest(results, pubdir) -> Manifest:
    return verify_public_record(results, pubdir, 'manifest')

def verify_ceremony_details(results, pubdir) -> CeremonyDetails:
    return verify_public_record(results, pubdir, 'ceremony_details')

def verify_gather_announce(results, pubdir) -> bool:
    manifest = verify(results, pubdir, 'manifest')
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    return True

def verify_one_guardian_pubkey(results, pubdir, guardian_id) -> ElectionPublicKey:
    # TODO what was this for?
    # ceremony_details = verify(results, pubdir, 'ceremony_details')
    # TODO explicitly say that kwargs needs guardian_id?
    return verify_public_record(
        results, pubdir, 'guardian_pubkey',
        guardian_id=guardian_id
    )

def verify_one_guardian_backup(results, pubdir):
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    raise NotImplementedError

def verify_one_guardian_verification(results, pubdir):
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    one_guardian_backup = verify(results, pubdir, 'one_guardian_backup')
    raise NotImplementedError

def verify_joint_key(results, pubdir):
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_constants(results, pubdir):
    build_election = verify(results, pubdir, 'build_election')
    raise NotImplementedError

def verify_context(results, pubdir):
    build_election = verify(results, pubdir, 'build_election')
    raise NotImplementedError

def verify_one_device(results, pubdir):
    raise NotImplementedError

def verify_one_ballot_submitted(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    raise NotImplementedError

def verify_one_cast_notice(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    raise NotImplementedError

def verify_one_ballot_spoiled(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    raise NotImplementedError

def verify_ciphertext_tally(results, pubdir):
    context = verify(results, pubdir, 'context')
    internal_manifest = verify(results, pubdir, 'internal_manifest')
    all_ballots_cast = verify(results, pubdir, 'all_ballots_cast')
    raise NotImplementedError

def verify_one_tally_share(results, pubdir):
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    context = verify(results, pubdir, 'context')
    ciphertext_tally = verify(results, pubdir, 'ciphertext_tally')
    raise NotImplementedError

def verify_one_spoiled_share(results, pubdir):
    context = verify(results, pubdir, 'context')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    raise NotImplementedError

def verify_plaintext_tally(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    context = verify(results, pubdir, 'context')
    ciphertext_tally = verify(results, pubdir, 'ciphertext_tally')
    all_tally_shares = verify(results, pubdir, 'all_tally_shares')
    raise NotImplementedError

def verify_one_spoiled_result(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    context = verify(results, pubdir, 'context')
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    one_spoiled_share = verify(results, pubdir, 'one_spoiled_share')
    one_spoiled_share = verify(results, pubdir, 'one_spoiled_share')
    raise NotImplementedError

def verify_all_guardian_pubkeys(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    raise NotImplementedError

def verify_all_ballots_submitted(results, pubdir):
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    raise NotImplementedError

def verify_all_ballots_spoiled(results, pubdir):
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    raise NotImplementedError

def verify_all_cast_notices(results, pubdir):
    one_cast_notice = verify(results, pubdir, 'one_cast_notice')
    raise NotImplementedError

def verify_all_spoiled_shares(results, pubdir):
    one_spoiled_share = verify(results, pubdir, 'one_spoiled_share')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_all_spoiled_results(results, pubdir):
    one_spoiled_result = verify(results, pubdir, 'one_spoiled_result')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_all_tally_shares(results, pubdir):
    one_tally_share = verify(results, pubdir, 'one_tally_share')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_build_election(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    joint_key = verify(results, pubdir, 'joint_key')
    raise NotImplementedError

def verify_internal_manifest(results, pubdir):
    build_election = verify(results, pubdir, 'build_election')
    raise NotImplementedError

def verify_all_guardian_backups(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    one_guardian_backup = verify(results, pubdir, 'one_guardian_backup')
    raise NotImplementedError

def verify_all_guardian_verifications(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    one_guardian_verification = verify(results, pubdir, 'one_guardian_verification')
    raise NotImplementedError

def verify_all_devices(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    raise NotImplementedError

def verify_all_ballots_cast(results, pubdir):
    raise NotImplementedError

def verify_gather_ceremony(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    joint_key = verify(results, pubdir, 'joint_key')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    all_guardian_backups = verify(results, pubdir, 'all_guardian_backups')
    all_guardian_verifications = verify(results, pubdir, 'all_guardian_verifications')
    raise NotImplementedError

def verify_gather_constants(results, pubdir):
    joint_key = verify(results, pubdir, 'joint_key')
    constants = verify(results, pubdir, 'constants')
    context = verify(results, pubdir, 'context')
    raise NotImplementedError

def verify_gather_config(results, pubdir):
    all_devices = verify(results, pubdir, 'all_devices')
    gather_announce = verify(results, pubdir, 'gather_announce')
    gather_ceremony = verify(results, pubdir, 'gather_ceremony')
    gather_constants = verify(results, pubdir, 'gather_constants')
    raise NotImplementedError

def verify_gather_ballots(results, pubdir):
    all_ballots_submitted = verify(results, pubdir, 'all_ballots_submitted')
    all_ballots_spoiled = verify(results, pubdir, 'all_ballots_spoiled')
    all_cast_notices = verify(results, pubdir, 'all_cast_notices')
    all_spoiled_results = verify(results, pubdir, 'all_spoiled_results')
    raise NotImplementedError

def verify_gather_decryptions(results, pubdir):
    plaintext_tally = verify(results, pubdir, 'plaintext_tally')
    all_spoiled_results = verify(results, pubdir, 'all_spoiled_results')
    raise NotImplementedError

def verify_gather_election(results, pubdir):
    gather_config = verify(results, pubdir, 'gather_config')
    gather_ballots = verify(results, pubdir, 'gather_ballots')
    gather_decryptions = verify(results, pubdir, 'gather_decryptions')
    raise NotImplementedError


def verify_public_record(
    results: ResultsCache, pubdir: str, recname: TargetName, **fmtargs
) -> Union[Failure, Success]:
    "Wrap from_public_record with verification stuff"
    if len(fmtargs) == 0:
        # we normally want to use recname,
        # but custom msg is better for ballots and other things with ids
        # TODO back to custom msg passsed here?
        msg = recname
    else:
        msg = f'{recname} {fmtargs}'
    try:
        result = from_public_record(pubdir, recname, **fmtargs)
        print(f'✅ {msg}')
        return result
    except Exception as e:
        print(f'❌ {msg}')
        raise

def verify(results: ResultsCache, pubdir: str, recname: TargetName, **kwargs):
    """
    Main verify function that calls the others with caching etc
    `results` is the main program state
    `pubdir` is the public_records dir
    `pubrec` is a key in the PUBLIC_RECORDS map
    """

    # memoize
    # note this could sort of be done using functools.cache,
    # except that wouldn't also accumulate errors
    kwargs_frozen = freeze_kwargs(kwargs)
    if recname in results and kwargs_frozen in results[recname]:
        print(f'using memoized {recname} {kwargs}')
        return results[recname][kwargs_frozen]

    # find and call the verify_ function,
    # capturing logs + errors
    verify_fn = globals()[f'verify_{recname}']
    with CaptureLog(level=logging.DEBUG) as log:
        try:
            if len(kwargs) == 0:
                result = verify_fn(results, pubdir)
            else:
                result = verify_fn(results, pubdir, **kwargs)
        except Exception as e:
            msgs = [str(e)]
            msgs.append(log.getvalue().strip())
            result = ' '.join(msgs)

    # cache result
    if not recname in results:
        results[recname] = {}
    results[recname][kwargs_frozen] = result


### cli ###

def main(pubdir, verifier_id):

    # main state is a dict of artifact_name -> fmtargs -> either str or result
    # it accumulates both successful result objects and error messages
    results: ResultsCache = {}

    print('verifying public election artifacts...\n')

    verify(results, pubdir, 'gather_announce')
    verify(results, pubdir, 'one_guardian_pubkey', guardian_id='guardian_1')
    verify(results, pubdir, 'one_guardian_pubkey', guardian_id='guardian_2')
    verify(results, pubdir, 'one_guardian_pubkey', guardian_id='guardian_3')

    # TODO summary here
    print()
    # pprint(results)
    pprint(results.keys())
    pprint(results['one_guardian_pubkey'].keys())


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

