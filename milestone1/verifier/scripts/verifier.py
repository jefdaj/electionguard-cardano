#!/usr/bin/env python3

# TODO add nodes for checking all the ballots are accounted for!

import time
import click
from typing import Any, Union, Optional, Callable, List, Dict, Tuple
from collections import defaultdict
from utils import (
    build_election,
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
    list_device_numbers,
)
import logging
from pprint import pprint

from electionguard.manifest import Manifest
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionJointKey,
    # ElectionKeyPair,
    ElectionPublicKey,
    ElectionPartialKeyBackup,
    ElectionPartialKeyVerification,
    # combine_election_public_keys,
    # generate_election_key_pair,
    # generate_election_partial_key_backup,
    # verify_election_partial_key_backup
)
from electionguard.constants import ElectionConstants
from electionguard.manifest import Manifest, InternalManifest
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice


### utils ###

# TODO util functions to use that type easily

# normally one of the keys in the PUBLIC_RECORDS map,
# but might also be prefixed with , all_, gather_, etc.
TargetName = str

# any extra arguments needed to identify a record (guardian_id etc)
# has to be frozen (hashable) to go in results below
TargetArgs = Tuple[Tuple[str, Any]]

# from https://stackoverflow.com/a/2704866
def freeze_kwargs(kwargs):
    return tuple(sorted(kwargs.items()))

# error message
Failure = str

# successfully verified public record
Success = Any

# main state of the verify program
ResultsCache = Dict[
    TargetName,
    Dict[TargetArgs,
         Union[Failure, Success]
    ]
]

class DependencyError(Exception):
    "Make a target fail when one or more of its deps does"

def verify_deps(**deps):
    "Make a target fail when one or more of its deps does"
    errors = {k:v for (k,v) in deps.items() if isinstance(v, Failure)}
    n_errors = len(errors)
    # print(errors)
    if n_errors > 0:
        e = DependencyError(f'{n_errors} dependencies failed')
        print(errors)
        # print(e) # TODO handle this in verify()
        raise e
    return deps


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
    print('\nannouncement:')
    deps = verify_deps(
        manifest = verify(results, pubdir, 'manifest'),
        ceremony_details = verify(results, pubdir, 'ceremony_details'),
    )
    return True

def verify_guardian_pubkey(results, pubdir, guardian_id) -> ElectionPublicKey:
    # TODO why isn't this recording results?
    res =  verify_public_record(
        results, pubdir, 'guardian_pubkey',
        guardian_id=guardian_id
    )
    return res

def verify_guardian_backup(results, pubdir, guardian_id, backup_order) -> ElectionPartialKeyBackup:
    # TODO verify the backup corresponds to the key
    deps = verify_deps(
        guardian_pubkey = verify(results, pubdir, 'guardian_pubkey', guardian_id=guardian_id),
    )
    return verify_public_record(
        results, pubdir, 'guardian_backup',
        guardian_id=guardian_id, backup_order=backup_order
    )

def verify_guardian_verification(results, pubdir, guardian_id, backup_order) -> ElectionPartialKeyVerification:
    # TODO verify the verification corresponds to the backup
    deps = verify_deps(
        guardian_pubkey = verify(
            results, pubdir, 'guardian_pubkey',
            guardian_id=guardian_id
        ),
        guardian_backup = verify(
            results, pubdir, 'guardian_backup',
            guardian_id=guardian_id, backup_order=backup_order
        ),
    )
    return verify_public_record(
        results, pubdir, 'guardian_verification',
        guardian_id=guardian_id, backup_order=backup_order
    )

def verify_joint_key(results, pubdir) -> ElectionJointKey:
    # TODO add verification that joint_key derives from the pubkeys!
    deps = verify_deps(
        all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys'),
    )
    return verify_public_record(results, pubdir, 'joint_key')

# TODO use longer IDs rather than sequential small numbers?
def verify_device(results, pubdir, device_number) -> EncryptionDevice:
    return verify_public_record(
        results, pubdir, 'device',
        device_number=device_number
    )

def verify_all_devices(results, pubdir) -> List[EncryptionDevice]:
    print('\nencryption devices:')
    deps = verify_deps(**{
        f'device_{n}': verify(results, pubdir, 'device', device_number=n)
        for n in list_device_numbers(pubdir)
    })
    return deps.values()

def verify_ballot_submitted(results, pubdir):
    device = verify(results, pubdir, 'device')
    raise NotImplementedError

def verify_cast_notice(results, pubdir):
    device = verify(results, pubdir, 'device')
    ballot_submitted = verify(results, pubdir, 'ballot_submitted')
    raise NotImplementedError

def verify_ballot_spoiled(results, pubdir):
    device = verify(results, pubdir, 'device')
    ballot_submitted = verify(results, pubdir, 'ballot_submitted')
    raise NotImplementedError

def verify_ciphertext_tally(results, pubdir):
    context = verify(results, pubdir, 'context')
    internal_manifest = verify(results, pubdir, 'internal_manifest')
    all_cast_notices = verify(results, pubdir, 'all_cast_notices')
    raise NotImplementedError

def verify_tally_share(results, pubdir):
    guardian_pubkey = verify(results, pubdir, 'guardian_pubkey')
    context = verify(results, pubdir, 'context')
    ciphertext_tally = verify(results, pubdir, 'ciphertext_tally')
    raise NotImplementedError

def verify_spoiled_share(results, pubdir):
    context = verify(results, pubdir, 'context')
    ballot_submitted = verify(results, pubdir, 'ballot_submitted')
    ballot_submitted = verify(results, pubdir, 'ballot_submitted')
    ballot_spoiled = verify(results, pubdir, 'ballot_spoiled')
    raise NotImplementedError

def verify_plaintext_tally(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    context = verify(results, pubdir, 'context')
    ciphertext_tally = verify(results, pubdir, 'ciphertext_tally')
    all_tally_shares = verify(results, pubdir, 'all_tally_shares')
    raise NotImplementedError

def verify_spoiled_result(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    context = verify(results, pubdir, 'context')
    ballot_spoiled = verify(results, pubdir, 'ballot_spoiled')
    ballot_spoiled = verify(results, pubdir, 'ballot_spoiled')
    spoiled_share = verify(results, pubdir, 'spoiled_share')
    spoiled_share = verify(results, pubdir, 'spoiled_share')
    raise NotImplementedError

# TODO should this be a list or dict?
def verify_all_guardian_pubkeys(results, pubdir) -> List[ElectionPublicKey]:
    ceremony_details = verify(results, pubdir, 'ceremony_details') # TODO error here?
    pubkeys = []
    # print('\nall guardian pubkeys:')
    for n in range(1, ceremony_details.number_of_guardians+1):
        guardian_id = f'guardian_{n}'
        pubkey = verify(results, pubdir, 'guardian_pubkey', guardian_id=guardian_id)
        pubkeys.append(pubkey)
    return pubkeys

def verify_all_ballots_submitted(results, pubdir):
    ballot_submitted = verify(results, pubdir, 'ballot_submitted')
    raise NotImplementedError

def verify_all_ballots_spoiled(results, pubdir):
    ballot_spoiled = verify(results, pubdir, 'ballot_spoiled')
    raise NotImplementedError

def verify_all_cast_notices(results, pubdir):
    cast_notice = verify(results, pubdir, 'cast_notice')
    raise NotImplementedError

def verify_all_spoiled_shares(results, pubdir):
    spoiled_share = verify(results, pubdir, 'spoiled_share')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_all_spoiled_results(results, pubdir):
    spoiled_result = verify(results, pubdir, 'spoiled_result')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_all_tally_shares(results, pubdir):
    tally_share = verify(results, pubdir, 'tally_share')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_build_election(results, pubdir) -> \
    Tuple[
        ElectionConstants,
        InternalManifest,
        CiphertextElectionContext
    ]:
    deps = verify_deps(
        ceremony_details = verify(results, pubdir, 'ceremony_details'),
        manifest = verify(results, pubdir, 'manifest'),
        joint_key = verify(results, pubdir, 'joint_key'),
    )
    return build_election(
        deps['ceremony_details'],
        deps['manifest'],
        deps['joint_key'],
    )

def verify_constants(results, pubdir) -> ElectionConstants:
    deps = verify_deps(build_election = verify(results, pubdir, 'build_election'))
    (constants, _, _) = deps['build_election']
    return constants

def verify_internal_manifest(results, pubdir) -> InternalManifest:
    deps = verify_deps(build_election = verify(results, pubdir, 'build_election'))
    (_, internal_manifest, _) = deps['build_election']
    return internal_manifest

def verify_context(results, pubdir) -> CiphertextElectionContext:
    deps = verify_deps(build_election = verify(results, pubdir, 'build_election'))
    (_, _, context) = deps['build_election']
    return context

def verify_all_guardian_backups(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    backups = []
    # print('\nall guardian backups:')
    for gn in range(1, ceremony_details.number_of_guardians+1):
        for bo in range(1, ceremony_details.number_of_guardians+1):
            if gn == bo:
                continue
            guardian_id = f'guardian_{gn}'
            backup = verify(
                results, pubdir, 'guardian_backup',
                guardian_id=guardian_id, backup_order=bo
            )
        backups.append(backup)
    return backups

def verify_all_guardian_verifications(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    verifications = []
    # print('\nall guardian backup verifications:')
    for gn in range(1, ceremony_details.number_of_guardians+1):
        for bo in range(1, ceremony_details.number_of_guardians+1):
            if gn == bo:
                continue
            guardian_id = f'guardian_{gn}'
            verification = verify(
                results, pubdir, 'guardian_verification',
                guardian_id=guardian_id, backup_order=bo
            )
        verifications.append(verification)
    return verifications

def verify_gather_ceremony(results, pubdir) -> bool:
    print('\nkey ceremony:')
    deps = verify_deps(
        ceremony_details = verify(results, pubdir, 'ceremony_details'),
        all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys'),
        all_guardian_backups = verify(results, pubdir, 'all_guardian_backups'),
        all_guardian_verifications = verify(results, pubdir, 'all_guardian_verifications'),
        joint_key = verify(results, pubdir, 'joint_key'),
    )
    return True

# TODO rename other mentions of this as the "election" step, which was confusing ofc
def verify_gather_constants(results, pubdir) -> bool:
    # print('\nelection constants:') # TODO remove?
    deps = verify_deps(
        joint_key = verify(results, pubdir, 'joint_key'),
        constants = verify(results, pubdir, 'constants'),
        context = verify(results, pubdir, 'context'),
    )
    return True

def verify_gather_config(results, pubdir) -> bool:
    deps = verify_deps(
        gather_announce = verify(results, pubdir, 'gather_announce'),
        gather_ceremony = verify(results, pubdir, 'gather_ceremony'),
        gather_constants = verify(results, pubdir, 'gather_constants'),
        all_devices = verify(results, pubdir, 'all_devices'),
    )
    return True

def verify_gather_ballots(results, pubdir) -> bool:
    deps = verify_deps(
        all_ballots_submitted = verify(results, pubdir, 'all_ballots_submitted'),
        all_ballots_spoiled = verify(results, pubdir, 'all_ballots_spoiled'),
        all_cast_notices = verify(results, pubdir, 'all_cast_notices'),
        all_spoiled_results = verify(results, pubdir, 'all_spoiled_results'),
    )
    return True

def verify_gather_decryptions(results, pubdir) -> bool:
    deps = verify_deps(
        plaintext_tally = verify(results, pubdir, 'plaintext_tally'),
        all_spoiled_results = verify(results, pubdir, 'all_spoiled_results'),
    )
    return True

def verify_gather_election(results, pubdir) -> bool:
    deps = verify_deps(
        gather_config = verify(results, pubdir, 'gather_config'),
        gather_ballots = verify(results, pubdir, 'gather_ballots'),
        gather_decryptions = verify(results, pubdir, 'gather_decryptions'),
    )
    return True


def verify_public_record(
    results: ResultsCache, pubdir: str, target: TargetName, **fmtargs
) -> Union[Failure, Success]:
    "Wrap from_public_record with verification stuff"
    if len(fmtargs) == 0:
        # we normally want to use target,
        # but custom msg is better for ballots and other things with ids
        # TODO back to custom msg passsed here?
        msg = target
    else:
        msg = f'{target} {fmtargs}'
    try:
        result = from_public_record(pubdir, target, **fmtargs)
        print(f'✅ {msg}')
        return result
    except NotImplementedError as e:
        print(str(e))
        raise
    except Exception as e:
        print(f'❌ {msg}')
        raise

def verify(results: ResultsCache, pubdir: str, target: TargetName, **kwargs):
    """
    Main verify function that calls the others with caching etc
    `results` is the main program state
    `pubdir` is the public_records dir
    `pubrec` is a key in the PUBLIC_RECORDS map
    """

    kwargs_frozen = freeze_kwargs(kwargs)

    # memoize
    # note this could sort of be done using functools.cache,
    # except that wouldn't also accumulate errors
    if target in results:
        if kwargs_frozen in results[target]:
            # print(f'using memoized {target} {kwargs}')
            result = results[target][kwargs_frozen]
            return result

    # find and call the verify_ function,
    # capturing logs + errors
    verify_fn = globals()[f'verify_{target}']
    with CaptureLog(level=logging.DEBUG) as log:
        try:
            # if len(kwargs) == 0:
                # result = verify_fn(results, pubdir)
            # else:
            result = verify_fn(results, pubdir, **kwargs)
        # except DependencyError as e:
        #     print(f'skipped {target} because dependencies failed')
        except Exception as e:
            msgs = [str(e)]
            msgs.append(log.getvalue().strip())
            result = Failure(' '.join(msgs).strip())
            # print(f'err during {verify_fn.__name__}: "{result}"')

    # cache result
    if not target in results:
        results[target] = {}
    results[target][kwargs_frozen] = result

    return result


### cli ###

def main(pubdir, verifier_id):

    # main program state
    # accumulates successful result objects and error messages
    results: ResultsCache = {}

    verify(results, pubdir, 'gather_config')
    # verify(results, pubdir, 'gather_ceremony')
    # verify(results, pubdir, 'gather_constants')
    # verify(results, pubdir, 'gather_config')

    # TODO summary here
    print()
    # pprint(results)
    # pprint(results.keys())
    # pprint(results['gather_config'])
    # pprint(results['all_guardian_pubkeys'])
    # pprint(results['guardian_pubkey'].keys())
    # pprint(results['guardian_backup'])


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

