#!/usr/bin/env python3

import click
import logging
import time
import sys

from collections import defaultdict
from copy import deepcopy
from typing import Any, Union, Optional, Callable, List, Dict, Tuple

from utils import (
    build_election,
    list_submitted_ballot_fmtargs,
    list_cast_ballot_fmtargs,
    list_spoiled_ballot_fmtargs,
    list_guardian_backup_fmtargs,
    from_public_record,
    to_public_record,
    CaptureLog,
    list_device_numbers,
    record_basename,
    init_log,
)

from electionguard.ballot import CiphertextBallot, SubmittedBallot
from electionguard.ballot_box import (BallotBoxState, submit_ballot)
from electionguard.constants import ElectionConstants
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice
from electionguard.guardian import GuardianId
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionJointKey,
    ElectionPublicKey,
    ElectionPartialKeyBackup,
    ElectionPartialKeyVerification,
)
from electionguard.manifest import Manifest, InternalManifest
from electionguard.tally import (CiphertextTally, PlaintextTally)

from electionguard_verify import *


### utils ###

# normally one of the keys in the PUBLIC_RECORDS map,
# but might also be prefixed with , all_, gather_, etc.
TargetName = str

# any extra arguments needed to identify a record (guardian_id etc)
# has to be frozen (hashable) to go in results below
TargetArgs = Tuple[Tuple[str, Any]]

# from https://stackoverflow.com/a/2704866
def freeze_kwargs(kwargs):
    return tuple(sorted(kwargs.items()))

def unfreeze_kwargs(frozen_kwargs):
    # return {k:dict(v) for (k,v) in frozen_kwargs}
    return dict(frozen_kwargs)

# error message
Error = str

# successfully verified public record
Success = Any

# main state of the verify program
ResultsCache = Dict[
    TargetName,
    Dict[TargetArgs,
         Union[Error, Success]
    ]
]

# summary of just the failed results
Errors = Dict[
    TargetName,
    Dict[TargetArgs, Error]
]

Successes = Dict[
    TargetName,
    dict # TODO variant of Dict[TargetArgs, Success] that can go into a JSON
]

# flat summary of whether each top-level node was verified
# (not including the ones that are mapped over lots of files)
VerifiedBools = Dict[TargetName, bool]

class DependencyError(Exception):
    "Make a target fail when one or more of its deps does"

def verify_deps(**deps):
    "Make a target fail when one or more of its deps does"
    errors = {}
    for (k, v) in deps.items():
        if isinstance(v, dict):
            for (k2, v2) in v.items():
                if isinstance(v2, Error):
                    if not k in errors:
                        errors[k] = {}
                    errors[k][k2] = v2
        elif isinstance(v, Error):
            errors[k] = v
        # else drop the non-errors
    error_keys = ', '.join(sorted(errors.keys()))
    if len(errors) > 0:
        raise DependencyError(f'dependencies failed: {error_keys}')
    return deps

def verify_decryption_with_checkmark_message(
    msg: str,
    log: logging.Logger,
    plaintext_tally: PlaintextTally,
    all_guardian_pubkeys: Dict[GuardianId, ElectionPublicKey],
    context: CiphertextElectionContext,
) -> bool:
    def verify_closure():
        result = verify_decryption(plaintext_tally, all_guardian_pubkeys, context)
        if not result.verified:
            raise Exception(result.message)
        return True
    return with_checkmark_message(msg, verify_closure, log)


### verify_{name} verifies the {name} node in the dependency graph ###

def verify_manifest(results, pubdir, log) -> Manifest:
    return verify_public_record(results, pubdir, log, 'manifest')

def verify_ceremony_details(results, pubdir, log) -> CeremonyDetails:
    return verify_public_record(results, pubdir, log, 'ceremony_details')

def verify_gather_announce(results, pubdir, log) -> bool:
    log.info('Verifying announcement:')
    deps = verify_deps(
        manifest = verify(results, pubdir, log, 'manifest'),
        ceremony_details = verify(results, pubdir, log, 'ceremony_details'),
    )
    return True

def verify_guardian_pubkey(results, pubdir, log, guardian_id) -> ElectionPublicKey:
    res =  verify_public_record(
        results, pubdir, log, 'guardian_pubkey',
        guardian_id=guardian_id
    )
    return res

def verify_guardian_backup(results, pubdir, log, guardian_id, backup_order) -> ElectionPartialKeyBackup:
    # TODO verify the backup corresponds to the key
    deps = verify_deps(
        guardian_pubkey = verify(results, pubdir, log, 'guardian_pubkey', guardian_id=guardian_id),
    )
    return verify_public_record(
        results, pubdir, log, 'guardian_backup',
        guardian_id=guardian_id, backup_order=backup_order
    )

def verify_guardian_verification(results, pubdir, log, guardian_id, backup_order) -> ElectionPartialKeyVerification:
    # TODO verify the verification corresponds to the backup
    deps = verify_deps(
        guardian_pubkey = verify(
            results, pubdir, log, 'guardian_pubkey',
            guardian_id=guardian_id
        ),
        guardian_backup = verify(
            results, pubdir, log, 'guardian_backup',
            guardian_id=guardian_id, backup_order=backup_order
        ),
    )
    return verify_public_record(
        results, pubdir, log, 'guardian_verification',
        guardian_id=guardian_id, backup_order=backup_order
    )

def verify_joint_key(results, pubdir, log) -> ElectionJointKey:
    # TODO add verification that joint_key derives from the pubkeys!
    deps = verify_deps(
        all_guardian_pubkeys = verify(results, pubdir, log, 'all_guardian_pubkeys'),
    )
    return verify_public_record(results, pubdir, log, 'joint_key')

# TODO use longer IDs rather than sequential small numbers?
def verify_device(results, pubdir, log, device_number) -> EncryptionDevice:
    return verify_public_record(
        results, pubdir, log, 'device',
        device_number=device_number
    )

def verify_all_devices(results, pubdir, log) -> List[EncryptionDevice]:
    device_numbers = list_device_numbers(pubdir)
    log.info(f'\nVerifying {len(device_numbers)} encryption devices:')
    deps = verify_deps(**{
        f'device_{n}': verify(results, pubdir, log, 'device', device_number=n)
        for n in device_numbers
    })
    return deps.values()

def verify_ballot_submitted(results, pubdir, log, ballot_id) -> SubmittedBallot:
    # TODO verify it was submitted by one of the devices (or rely on Cardano for that?)
    # device = verify(results, pubdir, log, 'device')
    ballot = verify_public_record(
        results, pubdir, log, 'ballot_submitted',
        ballot_id=ballot_id
    )
    # We store the "submitted" ballots on chain as CiphertextBallot instead for now,
    # so they need to be marked submitted here after deserialization.
    # TODO store them as submitted instead?
    ballot_submitted = submit_ballot(ballot, BallotBoxState.UNKNOWN)
    return ballot_submitted

def verify_ballot_cast(results, pubdir, log, ballot_id) -> SubmittedBallot:
    # TODO verify it was submitted by one of the devices (or rely on Cardano for that?)
    # device = verify(results, pubdir, log, 'device')
    deps = verify_deps(
        ballot_submitted = verify(results, pubdir, log, 'ballot_submitted', ballot_id=ballot_id),
        cast_notice = verify_public_record(results, pubdir, log, 'cast_notice', ballot_id=ballot_id),
    )
    assert deps['cast_notice'].ballot_id == deps['ballot_submitted'].object_id
    # TODO verify time cast_at seems about right? (within a short window after submitted)
    # TODO post the actual cast ballots rather than copying submitted here?
    ballot_cast = deepcopy(deps['ballot_submitted'])
    ballot_cast.state = BallotBoxState.CAST # TODO submitted instead?

    return ballot_cast

def verify_ballot_spoiled(results, pubdir, log, ballot_id) -> SubmittedBallot:
    # TODO verify it was submitted by one of the devices (or rely on Cardano for that?)
    # device = verify(results, pubdir, log, 'device'),
    deps = verify_deps(
        ballot_submitted = verify(results, pubdir, log, 'ballot_submitted', ballot_id=ballot_id),
    )
    ballot_spoiled = verify_public_record(results, pubdir, log, 'ballot_spoiled', ballot_id=ballot_id)
    # We store the spoiled ballot as CiphertextBallot rather than
    # SubmittedBallot, because we want to publish the nonces. But that means we
    # need to officially "spoil" it here afer deserializing.
    # TODO is this actually needed for anything? spoiled ballots don't really need to be tallied
    assert ballot_spoiled.object_id == deps['ballot_submitted'].object_id
    ballot_submitted_v2 = submit_ballot(ballot_spoiled, BallotBoxState.SPOILED)
    # TODO verify they're identical except submitted has: all nonces set to null, state set to 999
    # TODO later, verify that the nonces decrypt to the expected votes (separate voter-side verifier)
    return ballot_submitted_v2

def verify_ciphertext_tally(results, pubdir, log):
    return verify_public_record(
        results, pubdir, log, 'ciphertext_tally',
        msg='ciphertext_tally format is valid'
    )

def verify_tally_aggregation(results, pubdir, log):
    deps = verify_deps(
        manifest = verify(results, pubdir, log, 'manifest'),
        context = verify(results, pubdir, log, 'context'),
        all_ballots_cast = verify(results, pubdir, log, 'all_ballots_cast'),
        # all_ballots_spoiled = verify(results, pubdir, log, 'all_ballots_spoiled'), # TODO remove?
        ciphertext_tally = verify(results, pubdir, log, 'ciphertext_tally'),
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
        f'ciphertext_tally is the correct aggregation of the {n_cast} cast ballots',
        verify_closure,
        log
    )

    return True

def verify_gather_tally(results, pubdir, log):
    log.info('\nVerifying final tally:')
    deps = verify_deps(
        ciphertext_tally = verify(results, pubdir, log, 'ciphertext_tally'),
        tally_aggregation = verify(results, pubdir, log, 'tally_aggregation'),
        plaintext_tally = verify(results, pubdir, log, 'plaintext_tally'),
        tally_decryption = verify(results, pubdir, log, 'tally_decryption'),
    )
    return True

def verify_plaintext_tally(results, pubdir, log):
    return verify_public_record(
        results, pubdir, log, 'plaintext_tally',
        msg='plaintext_tally format is valid'
    )

def verify_tally_decryption(results, pubdir, log) -> PlaintextTally:
    # TODO also verify that the shares == their corresponding public record files
    # TODO and that the published shares match the ciphertext_tally? is that possible?
    deps = verify_deps(
        plaintext_tally = verify(results, pubdir, log, 'plaintext_tally'),
        all_guardian_pubkeys = verify(results, pubdir, log, 'all_guardian_pubkeys'),
        context = verify(results, pubdir, log, 'context'),
    )
    verify_decryption_with_checkmark_message(
        'plaintext_tally guardian decryption shares are valid',
        log=log,
        **deps
    )
    return deps['plaintext_tally']

def verify_spoiled_result(results, pubdir, log, **fmtargs) -> PlaintextTally:
    deps = verify_deps(
        all_guardian_pubkeys = verify(results, pubdir, log, 'all_guardian_pubkeys'),
        context = verify(results, pubdir, log, 'context'),
    )
    spoiled_result = from_public_record(pubdir, 'spoiled_result', **fmtargs)
    # ballot_spoiled = from_public_record(pubdir, 'ballot_spoiled', **fmtargs),
    verify_decryption_with_checkmark_message(
        f'spoiled_result {fmtargs}',
        log=log,
        plaintext_tally=spoiled_result,
        all_guardian_pubkeys=deps['all_guardian_pubkeys'],
        context=deps['context'],
    )
    return spoiled_result

def verify_all_guardian_pubkeys(results, pubdir, log) -> Dict[GuardianId, ElectionPublicKey]:
    deps1 = verify_deps(
        ceremony_details = verify(results, pubdir, log, 'ceremony_details'),
    )
    deps2 = verify_deps(**{
        f'guardian_{n}': verify(results, pubdir, log, 'guardian_pubkey', guardian_id=f'guardian_{n}')
        for n in range(1, deps1['ceremony_details'].number_of_guardians+1)
    })
    return deps2

def verify_all_ballots_submitted(results, pubdir, log) -> List[SubmittedBallot]:
    fmtargs_list = list_submitted_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} submitted ballots:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'ballot_submitted', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()

def verify_all_ballots_spoiled(results, pubdir, log) -> List[SubmittedBallot]:
    fmtargs_list = list_spoiled_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} spoiled ballots:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'ballot_spoiled', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()

def verify_all_ballots_cast(results, pubdir, log) -> List[SubmittedBallot]:
    fmtargs_list = list_cast_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} cast ballots:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'ballot_cast', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()

def verify_all_spoiled_results(results, pubdir, log) -> List[PlaintextTally]:
    fmtargs_list = list_spoiled_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} spoiled ballot decyptions:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'spoiled_result', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()


def verify_build_election(results, pubdir, log) -> \
    Tuple[
        ElectionConstants,
        InternalManifest,
        CiphertextElectionContext
    ]:
    deps = verify_deps(
        ceremony_details = verify(results, pubdir, log, 'ceremony_details'),
        manifest = verify(results, pubdir, log, 'manifest'),
        joint_key = verify(results, pubdir, log, 'joint_key'),
    )
    return build_election(
        deps['ceremony_details'],
        deps['manifest'],
        deps['joint_key'],
    )

def verify_constants(results, pubdir, log) -> ElectionConstants:
    deps = verify_deps(build_election = verify(results, pubdir, log, 'build_election'))
    constants = with_checkmark_message(
        'constants',
        lambda: deps['build_election'][0],
        log
    )
    return constants

def verify_internal_manifest(results, pubdir, log) -> InternalManifest:
    deps = verify_deps(build_election = verify(results, pubdir, log, 'build_election'))
    (_, internal_manifest, _) = deps['build_election']
    internal_manifest = with_checkmark_message(
        'internal_manifest',
        lambda: deps['build_election'][1],
        log
    )
    return internal_manifest

def verify_context(results, pubdir, log) -> CiphertextElectionContext:
    deps = verify_deps(build_election = verify(results, pubdir, log, 'build_election'))
    context = with_checkmark_message(
        'context',
        lambda: deps['build_election'][2],
        log
    )
    return context

def verify_all_guardian_backups(results, pubdir, log) -> List[ElectionPartialKeyBackup]:
    deps1 = verify_deps(
        ceremony_details = verify(results, pubdir, log, 'ceremony_details'),
    )
    n_guardians = deps1['ceremony_details'].number_of_guardians
    fmtargs_list = list_guardian_backup_fmtargs(pubdir, n_guardians)
    deps2 = verify_deps(**{
        record_basename('guardian_backup', **fmtargs):
            verify(results, pubdir, log, 'guardian_backup', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps2.values()

def verify_all_guardian_verifications(results, pubdir, log):
    ceremony_details = verify(results, pubdir, log, 'ceremony_details')
    verifications = []
    for gn in range(1, ceremony_details.number_of_guardians+1):
        for bo in range(1, ceremony_details.number_of_guardians+1):
            if gn == bo:
                continue
            guardian_id = f'guardian_{gn}'
            verification = verify(
                results, pubdir, log, 'guardian_verification',
                guardian_id=guardian_id, backup_order=bo
            )
        verifications.append(verification)
    return verifications

def verify_gather_ceremony(results, pubdir, log) -> bool:
    log.info('\nVerifying key ceremony:')
    deps = verify_deps(
        ceremony_details = verify(results, pubdir, log, 'ceremony_details'),
        all_guardian_pubkeys = verify(results, pubdir, log, 'all_guardian_pubkeys'),
        all_guardian_backups = verify(results, pubdir, log, 'all_guardian_backups'),
        all_guardian_verifications = verify(results, pubdir, log, 'all_guardian_verifications'),

        # this is sometimes called part of the ceremony,
        # but i prefer putting it in 3_constants because admin does it
        # joint_key = verify(results, pubdir, log, 'joint_key'),
    )
    return True

# TODO figure out a less confusing name for this... final details? specifics?
# TODO then rename to match in other scripts too
def verify_gather_constants(results, pubdir, log) -> bool:
    log.info('\nVerifying election constants:')
    deps = verify_deps(
        joint_key = verify(results, pubdir, log, 'joint_key'),
        constants = verify(results, pubdir, log, 'constants'),
        internal_manifest = verify(results, pubdir, log, 'internal_manifest'),
        context = verify(results, pubdir, log, 'context'),
    )
    return True

def verify_gather_config(results, pubdir, log) -> bool:
    deps = verify_deps(
        gather_announce = verify(results, pubdir, log, 'gather_announce'),
        gather_ceremony = verify(results, pubdir, log, 'gather_ceremony'),
        gather_constants = verify(results, pubdir, log, 'gather_constants'),
        all_devices = verify(results, pubdir, log, 'all_devices'),
    )
    return True

def verify_n_spoiled_decrypted(results, pubdir, log) -> bool:
    deps = verify_deps(
        all_ballots_spoiled = verify(results, pubdir, log, 'all_ballots_spoiled'),
        all_spoiled_results = verify(results, pubdir, log, 'all_spoiled_results'),
    )
    n_spoiled = len(deps['all_ballots_spoiled'])
    n_result  = len(deps['all_spoiled_results'])
    return verify_assertion(
        f'{n_spoiled} ballots spoiled = {n_result} ballots decrypted',
        n_spoiled == n_result,
        log
    )

def verify_n_cast_spoiled_submitted(results, pubdir, log) -> bool:
    deps = verify_deps(
        all_ballots_cast      = verify(results, pubdir, log, 'all_ballots_cast'),
        all_ballots_spoiled   = verify(results, pubdir, log, 'all_ballots_spoiled'),
        all_ballots_submitted = verify(results, pubdir, log, 'all_ballots_submitted'),
    )
    n_cast      = len(deps['all_ballots_cast'])
    n_spoiled   = len(deps['all_ballots_spoiled'])
    n_submitted = len(deps['all_ballots_submitted'])
    return verify_assertion(
        f'{n_cast} ballots cast + {n_spoiled} ballots spoiled = {n_submitted} ballots submitted',
        n_cast + n_spoiled == n_submitted,
        log
    )

def verify_set_spoiled_decrypted(results, pubdir, log) -> bool:
    deps = verify_deps(
        all_ballots_spoiled = verify(results, pubdir, log, 'all_ballots_spoiled'),
        all_spoiled_results = verify(results, pubdir, log, 'all_spoiled_results'),
    )
    spoiled_ids = set(b.object_id for b in deps['all_ballots_spoiled'])
    result_ids  = set(b.object_id for b in deps['all_spoiled_results'])
    return verify_assertion(
        'set(spoiled ballot IDs) = set(decrypted ballot IDs)',
        spoiled_ids == result_ids,
        log
    )

def verify_set_cast_spoiled_submitted(results, pubdir, log) -> bool:
    # TODO why isn't this short-circuiting the rest of the fn?
    deps = verify_deps(
        all_ballots_cast = verify(results, pubdir, log, 'all_ballots_cast'),
        all_ballots_spoiled = verify(results, pubdir, log, 'all_ballots_spoiled'),
        all_ballots_submitted = verify(results, pubdir, log, 'all_ballots_submitted'),
    )
    cast_ids      = set(b.object_id for b in deps['all_ballots_cast'])
    spoiled_ids   = set(b.object_id for b in deps['all_ballots_spoiled'])
    submitted_ids = set(b.object_id for b in deps['all_ballots_submitted'])
    return verify_assertion(
        'set(cast ballot IDs) + set(spoiled ballot IDs) = set(submitted ballot IDs)',
        cast_ids.union(spoiled_ids) == submitted_ids,
        log
    )

def verify_ballot_sets(results, pubdir, log) -> bool:
    "Make sure the various sets of ballot IDs match up (nothing missing or extra)"
    log.info('\nVerifying ballot ID sets:')
    deps = verify_deps(
        n_spoiled_decrypted = verify(results, pubdir, log, 'n_spoiled_decrypted'),
        n_cast_spoiled_submitted = verify(results, pubdir, log, 'n_cast_spoiled_submitted'),
        set_spoiled_decrypted = verify(results, pubdir, log, 'set_spoiled_decrypted'),
        set_cast_spoiled_submitted = verify(results, pubdir, log, 'set_cast_spoiled_submitted'),
    )
    # TODO explicitly assert that each list has all unique IDs?
    return True

def verify_gather_decryptions(results, pubdir, log) -> bool:
    deps = verify_deps(
        plaintext_tally = verify(results, pubdir, log, 'plaintext_tally'),
        all_spoiled_results = verify(results, pubdir, log, 'all_spoiled_results'),
    )
    return True

def verify_gather_election(results, pubdir, log) -> bool:
    deps = verify_deps(
        gather_config = verify(results, pubdir, log, 'gather_config'),
        ballot_sets = verify(results, pubdir, log, 'ballot_sets'),
        gather_decryptions = verify(results, pubdir, log, 'gather_decryptions'),
    )
    return True

def with_checkmark_message(msg, fn_call, log):
    try:
        result = fn_call()
        log.info(f'✅ {msg}')
        return result
    except Exception as e:
        log.error(f'❌ {msg}')
        raise

def verify_assertion(msg, assertion, log):
    # wrapper is required because you can't `assert` inside a lambda
    def assertion_fn():
        try:
            assert assertion
        except AssertionError as e:
            raise Exception(f'false: {msg}')
    return with_checkmark_message(msg, assertion_fn, log)

def verify_public_record(
    results: ResultsCache,
    pubdir: str,
    log: logging.Logger,
    target: TargetName,
    **fmtargs
) -> Union[Error, Success]:
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
            lambda: from_public_record(pubdir, target, **fmtargs),
            log
        )
        return result
    except Exception as e:
        raise

def verify(
    results: ResultsCache,
    pubdir: str,
    log: logging.Logger,
    target: TargetName,
    **kwargs
):
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
            result = results[target][kwargs_frozen]
            return result

    # find and call the verify_ function,
    # capturing logs + errors
    verify_fn = globals()[f'verify_{target}']
    with CaptureLog(level=logging.DEBUG) as log2:
        try:
            result = verify_fn(results, pubdir, log, **kwargs)
        except Exception as e:
            msgs = [str(e)]
            msgs.append(log2.getvalue().strip())
            result = Error(' '.join(msgs).strip())
            # print(f'err during {verify_fn.__name__}: "{result}"')

    # cache result
    if not target in results:
        results[target] = {}
    results[target][kwargs_frozen] = result

    return result


### summary ###

def simplify_and_partition(results: ResultsCache, log: logging.Logger) \
        -> (Successes, Errors, VerifiedBools):

    successes: Successes = {}
    errors: Errors = {}
    bools: VerifiedBools = {}

    # simplify
    results2 = {}
    for (k,v) in results.items():

        # special cases/warts
        if k == 'ballot_cast':
            k = 'cast_notice'

        # remove trivial kwargs
        if list(v.keys()) == [()]:
            v2 = list(v.values())[0]
            results2[k] = v2

        # convert kwargs to their public record basenames
        else:
            results2[k] = {}
            for (k2, v2) in v.items():
                fmtargs = unfreeze_kwargs(k2)
                fname = record_basename(k, **fmtargs)
                results2[k][fname] = v2

    # partition
    for (target_name, result) in results2.items():
        if isinstance(result, Error):
            errors[target_name] = result
            bools[target_name] = False
            # log.info(f'{target_name} goes in errors')
            log.info(f'{target_name} error: {result}')
        elif isinstance(result, dict):
            successes_dict = {
                k:v for (k,v)
                in result.items()
                if not isinstance(v, Error)
            }
            errors_dict = {
                k:v for (k,v)
                in result.items()
                if isinstance(v, Error)
            }
            if len(errors_dict) > 0:
                errors[target_name] = errors_dict
                # log.info(f'some of {target_name} goes in errors')
            if len(successes_dict) > 0:
                successes[target_name] = successes_dict
                # log.info(f'some of {target_name} goes in successes')
        else:
            # should be a single success or a list
            successes[target_name] = result
            bools[target_name] = True
            # log.info(f'{target_name} goes in successes')

    log.debug(f'successes keys: {successes.keys()}')
    log.debug(f'errors keys: {errors.keys()}')

    return (successes, errors, bools)

def summarize_results(
    successes: Successes,
    errors: Errors,
    bools: VerifiedBools,
    pubdir: str,
    log: logging.Logger,
    verifier_id: str,
):
    n_errors = sum(
        1  if isinstance(v, Error) else len(v)
        for v in errors.values()
    )

    # no particular format, except it must be json-serializable
    # TODO codify it as a dataclass?
    summary = defaultdict(lambda: {})

    tally_header   = "Final tally of cast ballots"
    spoiled_header = 'Individual spoiled ballots'
    spoiled_summaries = {}
    try:

        log.info('\n' + spoiled_header + ':')

        spoiled_results = successes['all_spoiled_results']
        manifest        = successes['manifest']
        selection_names = manifest.get_selection_names("en")
        contest_names   = manifest.get_contest_names()

        for spoiled_result in spoiled_results:
            log.info('')
            if isinstance(spoiled_result, Error):
                continue
            ballot_id = spoiled_result.object_id
            short_id  = ballot_id[ballot_id.find('-')+1:]
            log.info(short_id)
            ballot_summary = []
            for contest in spoiled_result.contests.values():
                question = contest_names.get(contest.object_id)
                selected = [
                    selection_names[selection.object_id]
                    for selection in contest.selections.values()
                    if selection.tally > 0
                ]
                assert len(selected) < 2 # for a one of m contest
                try:
                    answer = selected[0]
                except IndexError:
                    answer = 'No answer' # TODO is this allowed?
                log.info(f'  {question} {answer}')
                contest_summary = {question: answer}
                ballot_summary.append(contest_summary)
            spoiled_summaries[short_id] = ballot_summary

        log.info('\n' + tally_header + ':\n')
        tally_result    = successes['plaintext_tally']
        tally_summary = []
        contest_summaries = []
        for tally_contest in tally_result.contests.values():
            contest_name = contest_names.get(tally_contest.object_id)
            contest_summary = {
                'question': contest_name,
                'answers': {},
            }
            log.info(contest_name)
            values = list(tally_contest.selections.values())
            values.sort(key=lambda v: v.tally, reverse=True)
            for selection in values:
                name = selection_names[selection.object_id]
                log.info(f"  {name} {selection.tally}")
                contest_summary['answers'][name] = selection.tally
            tally_summary.append(contest_summary)

    except Exception as e:
        tally_summary     = 'Unable to summarize tally'
        spoiled_summaries = 'Unable to summarize individual spoiled ballots'
        log.error('Unable to summarize individual spoiled ballots')
        log.error(e)
        n_errors += 1 # TODO is this a reasonable way to do it?

    # save summary json
    # no particular format, except it must be a json-serializable dict
    summary = {
        'Verified': bools,
        'Errors': errors,
        tally_header  : tally_summary,
        spoiled_header: spoiled_summaries,
    }
    to_public_record(pubdir, 'summary', summary, verifier_id=verifier_id)
    log.info('')

    if n_errors == 0:
        log.info('🎉 The election has been verified!')
    else:
        msgs = [
            'The election could NOT be verified!',
            f'There were {n_errors} errors.',
            f'See {verifier_id}.json for details.',
        ]
        log.error('\n'.join('⛔ ' + m for m in msgs))


### cli ###

def main(pubdir, log, verifier_id):

    # main program state
    # accumulates successful result objects and error messages
    results: ResultsCache = {}

    # these partially overlap, which is fine
    verify(results, pubdir, log, 'gather_config')
    verify(results, pubdir, log, 'all_ballots_submitted')
    verify(results, pubdir, log, 'all_ballots_cast')
    verify(results, pubdir, log, 'all_ballots_spoiled')
    verify(results, pubdir, log, 'all_spoiled_results')
    verify(results, pubdir, log, 'ballot_sets')
    verify(results, pubdir, log, 'gather_tally')
    verify(results, pubdir, log, 'gather_decryptions')
    verify(results, pubdir, log, 'gather_election')

    (successes, errors, bools) = simplify_and_partition(results, log)

    summarize_results(
        successes, errors, bools,
        pubdir, log, verifier_id,
    )

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
@click.option(
    "--logfile",
    prompt="Logfile (default: stdout)",
    help="Where to log printed messages",
    type=click.STRING,
)
def VerifyCommand(
    public_dir: str,
    verifier_id: str,
    logfile: Optional[str],
) -> None:
    """Verify all public election artifacts."""
    # TODO parse and pass cfg here
    log = init_log(logfile, logging.INFO)
    try:
        main(public_dir, log, verifier_id)
    except Exception as e:
        log.error(e)
        raise

@click.group
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()

