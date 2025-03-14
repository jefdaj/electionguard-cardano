#!/usr/bin/env python3

# TODO add nodes for checking all the ballots are accounted for!

import time
import click
from copy import deepcopy
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
    list_submitted_ballot_fmtargs,
    list_cast_ballot_fmtargs,
    list_spoiled_ballot_fmtargs,
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
from electionguard.guardian import GuardianId
from electionguard.manifest import Manifest, InternalManifest
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice
from electionguard.ballot import CiphertextBallot, SubmittedBallot
from electionguard.ballot_box import (BallotBoxState, submit_ballot)
from electionguard.tally import (CiphertextTally, PlaintextTally)

from electionguard_verify import *

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

def verify_decryption_with_checkmark_message(
    msg: str,
    plaintext_tally: PlaintextTally,
    all_guardian_pubkeys: Dict[GuardianId, ElectionPublicKey],
    context: CiphertextElectionContext,
) -> bool:
    def verify_closure():
        result = verify_decryption(plaintext_tally, all_guardian_pubkeys, context)
        if not result.verified:
            raise Exception(result.message)
        return True
    return with_checkmark_message(msg, verify_closure)


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
    print('\nverifying announcement:')
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
    device_numbers = list_device_numbers(pubdir)
    print(f'\nverifying {len(device_numbers)} encryption devices:')
    deps = verify_deps(**{
        f'device_{n}': verify(results, pubdir, 'device', device_number=n)
        for n in device_numbers
    })
    return deps.values()

def verify_ballot_submitted(results, pubdir, ballot_id) -> SubmittedBallot:
    # TODO verify it was submitted by one of the devices (or rely on Cardano for that?)
    # device = verify(results, pubdir, 'device')
    ballot = verify_public_record(
        results, pubdir, 'ballot_submitted',
        ballot_id=ballot_id
    )
    # We store the "submitted" ballots on chain as CiphertextBallot instead for now,
    # so they need to be marked submitted here after deserialization.
    # TODO store them as submitted instead?
    ballot_submitted = submit_ballot(ballot, BallotBoxState.UNKNOWN)
    return ballot_submitted

def verify_ballot_cast(results, pubdir, ballot_id) -> SubmittedBallot:

    # TODO verify it was submitted by one of the devices (or rely on Cardano for that?)
    # device = verify(results, pubdir, 'device')

    deps = verify_deps(
        ballot_submitted = verify(results, pubdir, 'ballot_submitted', ballot_id=ballot_id),
        cast_notice = verify_public_record(results, pubdir, 'cast_notice', ballot_id=ballot_id),
    )

    assert deps['cast_notice'].ballot_id == deps['ballot_submitted'].object_id

    # TODO verify time cast_at seems about right? (within a short window after submitted)

    # TODO post the actual cast ballots rather than copying submitted here?
    ballot_cast = deepcopy(deps['ballot_submitted'])
    ballot_cast.state = BallotBoxState.CAST # TODO submitted instead?

    return ballot_cast

def verify_ballot_spoiled(results, pubdir, ballot_id) -> SubmittedBallot:
    # TODO verify it was submitted by one of the devices (or rely on Cardano for that?)

    deps = verify_deps(
        # device = verify(results, pubdir, 'device'),
        ballot_submitted = verify(results, pubdir, 'ballot_submitted', ballot_id=ballot_id),
        ballot_spoiled = verify_public_record(results, pubdir, 'ballot_spoiled', ballot_id=ballot_id)
    )
    # We store the spoiled ballot as CiphertextBallot rather than
    # SubmittedBallot, because we want to publish the nonces. But that means we
    # need to officially "spoil" it here afer deserializing.
    # TODO is this actually needed for anything? spoiled ballots don't really need to be tallied
    assert deps['ballot_spoiled'].object_id == deps['ballot_submitted'].object_id
    ballot_submitted_v2 = submit_ballot(deps['ballot_spoiled'], BallotBoxState.SPOILED)
    # TODO verify they're identical except submitted has: all nonces set to null, state set to 999

    return ballot_submitted_v2

def verify_ciphertext_tally(results, pubdir):
    return verify_public_record(
        results, pubdir, 'ciphertext_tally',
        msg='ciphertext_tally format is valid'
    )

def verify_tally_aggregation(results, pubdir):
    deps = verify_deps(
        manifest = verify(results, pubdir, 'manifest'),
        context = verify(results, pubdir, 'context'),
        all_ballots_cast = verify(results, pubdir, 'all_ballots_cast'),
        # all_ballots_spoiled = verify(results, pubdir, 'all_ballots_spoiled'), # TODO remove?
        ciphertext_tally = verify(results, pubdir, 'ciphertext_tally'),
    )

    n_cast = len(deps['all_ballots_cast'])

    def verify_closure():
        new_tally = CiphertextTally(
            "verify-tally", # TODO best practices for this object id?
            InternalManifest(deps['manifest']), # TODO no need for internal_manifest anywhere then?
            deps['context']
        )
        # TODO these need to be SubmittedBallots not CiphertextBallots?
        for ballot in deps['all_ballots_cast']: # + deps['all_ballots_spoiled']:
            assert(new_tally.append(ballot, should_validate=True))
        assert new_tally.contests == deps['ciphertext_tally'].contests

    with_checkmark_message(
        f'ciphertext_tally is the aggregation of the {n_cast} cast ballots',
        verify_closure
    )

    return True

def verify_gather_tally(results, pubdir):
    print('\nverifying final tally:')
    deps = verify_deps(
        ciphertext_tally = verify(results, pubdir, 'ciphertext_tally'),
        tally_aggregation = verify(results, pubdir, 'tally_aggregation'),
        plaintext_tally = verify(results, pubdir, 'plaintext_tally'),
        tally_decryption = verify(results, pubdir, 'tally_decryption'),
    )
    return True

def verify_plaintext_tally(results, pubdir):
    return verify_public_record(
        results, pubdir, 'plaintext_tally',
        msg='plaintext_tally format is valid'
    )

def verify_tally_decryption(results, pubdir):
    # TODO also verify that the shares == their corresponding public record files
    # TODO and that the published shares match the ciphertext_tally? is that possible?
    deps = verify_deps(
        plaintext_tally = verify(results, pubdir, 'plaintext_tally'),
        all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys'),
        context = verify(results, pubdir, 'context'),
    )
    return verify_decryption_with_checkmark_message(
        'plaintext_tally guardian decryption shares are valid',
        **deps
    )

def verify_spoiled_result(results, pubdir, **fmtargs) -> PlaintextTally:
    deps = verify_deps(
        all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys'),
        context = verify(results, pubdir, 'context'),
    )
    spoiled_result = from_public_record(pubdir, 'spoiled_result', **fmtargs)
    # ballot_spoiled = from_public_record(pubdir, 'ballot_spoiled', **fmtargs),
    verify_decryption_with_checkmark_message(
        f'spoiled_result {fmtargs}',
        plaintext_tally=spoiled_result,
        all_guardian_pubkeys=deps['all_guardian_pubkeys'],
        context=deps['context'],
    )
    return spoiled_result

# TODO should this be a list or dict?
def verify_all_guardian_pubkeys(results, pubdir) -> Dict[GuardianId, ElectionPublicKey]:
    ceremony_details = verify(results, pubdir, 'ceremony_details') # TODO error here?
    pubkeys = {}
    # print('\verifying nall guardian pubkeys:')
    for n in range(1, ceremony_details.number_of_guardians+1):
        guardian_id = f'guardian_{n}'
        pubkey = verify(results, pubdir, 'guardian_pubkey', guardian_id=guardian_id)
        pubkeys[guardian_id] = pubkey
    return pubkeys

def verify_all_ballots_submitted(results, pubdir) -> List[SubmittedBallot]:
    fmtargs_list = list_submitted_ballot_fmtargs(pubdir)
    print(f'\nverifying {len(fmtargs_list)} submitted ballots:')
    ballots = []
    for fmtargs in fmtargs_list:
        ballot = verify(results, pubdir, 'ballot_submitted', **fmtargs)
        ballots.append(ballot)
    assert len(ballots) == len(fmtargs_list)
    return ballots

def verify_all_ballots_spoiled(results, pubdir) -> List[SubmittedBallot]:
    fmtargs_list = list_spoiled_ballot_fmtargs(pubdir)
    print(f'\nverifying {len(fmtargs_list)} spoiled ballots:')
    ballots = []
    for fmtargs in fmtargs_list:
        ballot = verify(results, pubdir, 'ballot_spoiled', **fmtargs)
        ballots.append(ballot)
    assert len(ballots) == len(fmtargs_list)
    return ballots

def verify_all_ballots_cast(results, pubdir) -> List[SubmittedBallot]:
    fmtargs_list = list_cast_ballot_fmtargs(pubdir)
    print(f'\nverifying {len(fmtargs_list)} cast ballots:')
    ballots = []
    for fmtargs in fmtargs_list:
        ballot = verify(results, pubdir, 'ballot_cast', **fmtargs)
        ballots.append(ballot)
    assert len(ballots) == len(fmtargs_list)
    return ballots

def verify_all_spoiled_results(results, pubdir):
    fmtargs_list = list_spoiled_ballot_fmtargs(pubdir)
    print(f'\nverifying {len(fmtargs_list)} spoiled ballot decyptions:')
    ballots = []
    for fmtargs in fmtargs_list:
        ballot = verify(results, pubdir, 'spoiled_result', **fmtargs)
        ballots.append(ballot)
    assert len(ballots) == len(fmtargs_list)
    return ballots


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
    constants = with_checkmark_message(
        'constants',
        lambda: deps['build_election'][0]
    )
    return constants

def verify_internal_manifest(results, pubdir) -> InternalManifest:
    deps = verify_deps(build_election = verify(results, pubdir, 'build_election'))
    (_, internal_manifest, _) = deps['build_election']
    internal_manifest = with_checkmark_message(
        'internal_manifest',
        lambda: deps['build_election'][1]
    )
    return internal_manifest

def verify_context(results, pubdir) -> CiphertextElectionContext:
    deps = verify_deps(build_election = verify(results, pubdir, 'build_election'))
    context = with_checkmark_message(
        'context',
        lambda: deps['build_election'][2]
    )
    return context

def verify_all_guardian_backups(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    backups = []
    # print('\nverifying all guardian backups:')
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
    print('\nverifying key ceremony:')
    deps = verify_deps(
        ceremony_details = verify(results, pubdir, 'ceremony_details'),
        all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys'),
        all_guardian_backups = verify(results, pubdir, 'all_guardian_backups'),
        all_guardian_verifications = verify(results, pubdir, 'all_guardian_verifications'),

        # this is sometimes called part of the ceremony,
        # but i prefer putting it in 3_constants because admin does it
        # joint_key = verify(results, pubdir, 'joint_key'),
    )
    return True

# TODO figure out a less confusing name for this... final details? specifics?
# TODO then rename to match in other scripts too
def verify_gather_constants(results, pubdir) -> bool:
    print('\nverifying election constants:')
    deps = verify_deps(
        joint_key = verify(results, pubdir, 'joint_key'),
        constants = verify(results, pubdir, 'constants'),
        internal_manifest = verify(results, pubdir, 'internal_manifest'),
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

def verify_ballot_sets(results, pubdir) -> bool:
    "Make sure the various sets of ballot IDs match up (nothing missing or extra)"
    print('\nverifying ballot ID sets:')
    deps = verify_deps(
        all_ballots_submitted = verify(results, pubdir, 'all_ballots_submitted'),
        all_ballots_cast = verify(results, pubdir, 'all_ballots_cast'),
        all_ballots_spoiled = verify(results, pubdir, 'all_ballots_spoiled'),
        all_spoiled_results = verify(results, pubdir, 'all_spoiled_results'),
    )

    n_submitted = len(deps['all_ballots_submitted'])
    n_cast      = len(deps['all_ballots_cast'])
    n_spoiled   = len(deps['all_ballots_spoiled'])
    n_result    = len(deps['all_spoiled_results'])

    verify_assertion(
        f'{n_spoiled} ballots spoiled = {n_result} ballots decrypted',
        n_spoiled == n_result
    )
    verify_assertion(
        f'{n_cast} ballots cast + {n_spoiled} ballots spoiled = {n_submitted} ballots submitted',
        n_cast + n_spoiled == n_submitted,
    )

    submitted_ids = set(b.object_id for b in deps['all_ballots_submitted'])
    cast_ids      = set(b.object_id for b in deps['all_ballots_cast'])
    spoiled_ids   = set(b.object_id for b in deps['all_ballots_spoiled'])
    result_ids    = set(b.object_id for b in deps['all_spoiled_results'])

    verify_assertion(
        'set(spoiled ballot IDs) = set(decrypted ballot IDs)',
        spoiled_ids == result_ids,
    )

    verify_assertion(
        'set(cast ballot IDs) + set(spoiled ballot IDs) = set(submitted ballot IDs)',
        cast_ids.union(spoiled_ids) == submitted_ids,
    )

    # TODO explicitly assert that each list has all unique IDs?

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
        ballot_sets = verify(results, pubdir, 'ballot_sets'),
        gather_decryptions = verify(results, pubdir, 'gather_decryptions'),
    )
    return True

def with_checkmark_message(msg, fn_call):
    try:
        result = fn_call()
        print(f'✅ {msg}')
        return result
    except Exception as e:
        print(f'❌ {msg}')
        raise

def verify_assertion(msg, assertion):
    # wrapper is required because you can't `assert` inside a lambda
    def assertion_fn():
        assert assertion
    return with_checkmark_message(msg, assertion_fn)

def verify_public_record(
    results: ResultsCache, pubdir: str, target: TargetName, **fmtargs
) -> Union[Failure, Success]:
    "Wrap from_public_record with verification stuff"
    try:
        # If one of the kwargs is explicitly msg, that should be used.
        msg = fmtargs.pop('msg')
    except:
        # Otherwise, use target + fmtargs if any, and otherwise just target
        if len(fmtargs) == 0:
            msg = target
        else:
            msg = f'{target} {fmtargs}'
    try:
        result = with_checkmark_message(
            msg,
            lambda: from_public_record(pubdir, target, **fmtargs)
        )
        return result
    except NotImplementedError as e:
        print(str(e))
        raise
    except Exception as e:
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

    # these partially overlap, which is fine
    verify(results, pubdir, 'gather_config')
    verify(results, pubdir, 'all_ballots_submitted')
    verify(results, pubdir, 'all_ballots_cast')
    verify(results, pubdir, 'all_ballots_spoiled')
    verify(results, pubdir, 'all_spoiled_results')
    verify(results, pubdir, 'ballot_sets')
    verify(results, pubdir, 'gather_tally')
    verify(results, pubdir, 'gather_decryptions')
    verify(results, pubdir, 'gather_election')

    # TODO summary here
    print()


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

