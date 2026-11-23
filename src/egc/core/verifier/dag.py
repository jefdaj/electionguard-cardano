#!/usr/bin/env python3

# This file is for the DAG of verify_* functions. I found it helpful to
# separate them from the machinery for running them in verify.py

from copy import deepcopy

# TODO rewrite these to match current code
from .utils import (
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

from .utils2 import *

from electionguard.ballot import SubmittedBallot
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

def verify_all_devices(results, pubdir, log) -> list[EncryptionDevice]:
    device_numbers = list_device_numbers(pubdir)
    log.info(f'\nVerifying {len(device_numbers)} encryption devices:')
    deps = verify_deps(**{
        f'device_{n}': verify(results, pubdir, log, 'device', device_number=n)
        for n in device_numbers
    })
    return deps.values()

def verify_ballot_submitted(results, pubdir, log, ballot_id) -> SubmittedBallot:
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
        ciphertext_tally = verify(results, pubdir, log, 'ciphertext_tally'),
    )

    n_cast = len(deps['all_ballots_cast'])

    def verify_closure():
        new_tally = CiphertextTally(
            "verify-tally",
            InternalManifest(deps['manifest']),
            deps['context']
        )
        for ballot in deps['all_ballots_cast']:
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

def verify_all_guardian_pubkeys(results, pubdir, log) -> dict[GuardianId, ElectionPublicKey]:
    deps1 = verify_deps(
        ceremony_details = verify(results, pubdir, log, 'ceremony_details'),
    )
    deps2 = verify_deps(**{
        f'guardian_{n}': verify(results, pubdir, log, 'guardian_pubkey', guardian_id=f'guardian_{n}')
        for n in range(1, deps1['ceremony_details'].number_of_guardians+1)
    })
    return deps2

def verify_all_ballots_submitted(results, pubdir, log) -> list[SubmittedBallot]:
    fmtargs_list = list_submitted_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} submitted ballots:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'ballot_submitted', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()

def verify_all_ballots_spoiled(results, pubdir, log) -> list[SubmittedBallot]:
    fmtargs_list = list_spoiled_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} spoiled ballots:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'ballot_spoiled', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()

def verify_all_ballots_cast(results, pubdir, log) -> list[SubmittedBallot]:
    fmtargs_list = list_cast_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} cast ballots:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'ballot_cast', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()

def verify_all_spoiled_results(results, pubdir, log) -> list[PlaintextTally]:
    fmtargs_list = list_spoiled_ballot_fmtargs(pubdir)
    log.info(f'\nVerifying {len(fmtargs_list)} spoiled ballot decyptions:')
    deps = verify_deps(**{
        fmtargs['ballot_id']: verify(results, pubdir, log, 'spoiled_result', **fmtargs)
        for fmtargs in fmtargs_list
    })
    return deps.values()


def verify_build_election(results, pubdir, log) -> \
    tuple[
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

def verify_all_guardian_backups(results, pubdir, log) -> list[ElectionPartialKeyBackup]:
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
    deps = verify_deps(
        all_ballots_cast      = verify(results, pubdir, log, 'all_ballots_cast'),
        all_ballots_spoiled   = verify(results, pubdir, log, 'all_ballots_spoiled'),
        all_ballots_submitted = verify(results, pubdir, log, 'all_ballots_submitted'),
    )
    cast_ids      = set(b.object_id for b in deps['all_ballots_cast'])
    spoiled_ids   = set(b.object_id for b in deps['all_ballots_spoiled'])
    submitted_ids = set(b.object_id for b in deps['all_ballots_submitted'])

    missing_ids = submitted_ids.difference(cast_ids).difference(spoiled_ids)
    if len(missing_ids) > 0:
        log.error(f'missing cast/spoil notices: {missing_ids}')

    return verify_assertion(
        'set(cast ballot IDs) + set(spoiled ballot IDs) = set(submitted ballot IDs)',
        cast_ids.union(spoiled_ids) == submitted_ids,
        log
    )

def verify_ballot_sets(results, pubdir, log) -> bool:
    "Make sure the various sets of ballot IDs match up (nothing missing or extra)"
    log.info('\nVerifying ballot ID sets:')
    deps = verify_deps(
        n_spoiled_decrypted        = verify(results, pubdir, log, 'n_spoiled_decrypted'),
        n_cast_spoiled_submitted   = verify(results, pubdir, log, 'n_cast_spoiled_submitted'),
        set_spoiled_decrypted      = verify(results, pubdir, log, 'set_spoiled_decrypted'),
        set_cast_spoiled_submitted = verify(results, pubdir, log, 'set_cast_spoiled_submitted'),
    )
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
