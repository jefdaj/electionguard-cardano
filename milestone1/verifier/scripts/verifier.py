#!/usr/bin/env python3

import click

from dataclasses import dataclass
from typing import Dict, Optional, List
from pprint import pprint

from utils import (
    build_election,
    load_submitted_ballots,
    load_cast_ballots,
    load_tally_shares,
    load_spoiled_shares,
    load_spoiled_results,
    load_guardian_pubkeys,
    load_spoiled_ballots,
    to_public_record,
    from_public_record,
)


from electionguard.ballot import CiphertextBallot, SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.manifest import (
    InternalManifest,
    Manifest,
)
from electionguard.type import GuardianId
from electionguard.tally import PlaintextTally, CiphertextTally

import json
from pygments import highlight, lexers, formatters

import logging
import sys
from io import StringIO


### utils ###

# based on:
# docs.python.org/3/howto/logging-cookbook.html#using-a-context-manager-for-selective-logging
# gist.github.com/66Ton99/b13c2867adef506554a4
class CaptureLog:

    def __init__(self, level=None, close=True):
        self.logger = logging.getLogger('electionguard')
        self.log_buffer = StringIO()
        self.handler = logging.StreamHandler(self.log_buffer)
        self.level = level
        self.close = close

    def __enter__(self):

        # remove original handlers and add the temporary one
        self.old_handlers = list(h for h in self.logger.handlers)
        self.logger.handlers.clear()
        self.logger.addHandler(self.handler)

        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)

        # for use within the context manager block
        return self.log_buffer

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.close:
            self.handler.close()

        # remove temporary handler and put back the originals
        self.logger.handlers.clear()
        for h in self.old_handlers:
            self.logger.addHandler(h)

        # implicit return of None => don't swallow exceptions

# TODO unify with the one in local-election scripts
def print_colorful_json_obj(obj):
	# based on https://stackoverflow.com/a/32166163
	formatted_json = json.dumps(obj, indent=2)
	colorful_json = highlight(
		formatted_json,
		lexers.JsonLexer(),
		formatters.TerminalFormatter()
	)
	print(colorful_json)


### from electionguard_verify src ###

@dataclass
class Verification:
    """
    Representation of a verification result with an optional message
    """

    verified: bool
    """Verification successful?"""
    message: Optional[str]

def verify_ballot(
    ballot: CiphertextBallot,
    manifest: Manifest,
    context: CiphertextElectionContext,
) -> Verification:
    """
    Method to verify the validity of a ballot
    """

    if not ballot.is_valid_encryption(
        manifest.crypto_hash(),
        context.elgamal_public_key,
        context.crypto_extended_base_hash,
    ):
        return Verification(
            False,
            message=f"verify_ballot: mismatching ballot encryption {ballot.object_id}",
        )

    return Verification(True, message=None)

def verify_decryption(
    tally: PlaintextTally,
    election_public_keys: Dict[GuardianId, ElectionPublicKey],
    context: CiphertextElectionContext,
) -> Verification:
    for _, contest in tally.contests.items():
        for selection_id, selection in contest.selections.items():
            for share in selection.shares:
                election_public_key = election_public_keys.get(share.guardian_id).key
                if not share.proof.is_valid(
                    selection.message,
                    election_public_key,
                    share.share,
                    context.crypto_extended_base_hash,
                ):
                    return Verification(
                        False,
                        message=f"verify_decryption: {selection_id} selection is not valid",
                    )

    return Verification(True, message=None)

def verify_aggregation(
    submitted_ballots: List[SubmittedBallot],
    tally: CiphertextTally,
    manifest: Manifest,
    context: CiphertextElectionContext,
) -> Verification:
    new_tally = CiphertextTally("verify", InternalManifest(manifest), context)

    for ballot in submitted_ballots:
        new_tally.append(ballot, True)

    if (
        isinstance(tally, CiphertextTally)
        and new_tally.cast_ballot_ids == tally.cast_ballot_ids
        and new_tally.spoiled_ballot_ids == tally.spoiled_ballot_ids
        and new_tally.contests == tally.contests
    ):
        return Verification(True, message=None)

    return Verification(
        False,
        message="verify_aggregation: aggregated value of ballots doesn't matches with tally",
    )


### my verify code ###

def verify_ciphertext_ballots(ballots, header_msg, manifest, context) -> int:
    print(header_msg)
    errors = {}
    for ballot in ballots:
        print(f'  {ballot.object_id}...', end=' '),
        with CaptureLog(level=logging.DEBUG) as log:
            result = verify_ballot(ballot, manifest, context)
            if result.verified:
                print('ok')
            else:
                # print(f'ERROR {ballot.object_id} failed verification!')
                print('FAIL')
                msgs = []
                if result.message is not None:
                    msgs.append(result.message)
                msgs.append(log.getvalue().strip())
                errors[ballot.object_id] = ' '.join(msgs)
    print()
    return errors

def verify_load_ballots(public_dir, load_fn, error_dict, error_name):
    try:
        ballots = load_fn(public_dir)
        ballot_ids = set(b.object_id for b in ballots)
        n_loaded = len(ballot_ids)
        return (ballots, ballot_ids, n_loaded)
    except FileNotFoundError as e:
        error_dict[error_name]['verify_load_ballots'] = str(e)
        raise

def verify_predicate(predicate, header_msg, error_dict, error_name):
    try:
        print(header_msg + '...', end=' ')
        assert predicate
        print('ok')
    except Exception as e:
        print('FAIL')
        error_dict[error_name] = str(e)

# TODO pass cfg here
def verify_election(public_dir):

    # custom dict to build up a report
    # TODO codify it as a class?
    errors = {
        'cast_ballots': {},
        'spoiled_ballots': {},
        'ballots_accounted_for': {},
    }

    all_ballots_loaded = True
    finished_verifying = True

    # TODO handle these not existing too
    manifest  = from_public_record(public_dir, 'manifest')
    details   = from_public_record(public_dir, 'ceremony_details')
    joint_key = from_public_record(public_dir, 'joint_key')
    (_, _, context) = build_election(details, manifest, joint_key)


    # TODO handle these not existing too? might be silent unless they're all missing
    submitted_ballots = load_submitted_ballots(public_dir)
    submitted_ballot_ids = set(b.object_id for b in submitted_ballots)
    n_submitted = len(submitted_ballot_ids)

    try:
        (cast_ballots, cast_ballot_ids, n_cast) = verify_load_ballots(
            public_dir, load_cast_ballots, errors, 'cast_ballots'
        )
        cast_ballots_loaded = True
        errors['cast_ballots'] = verify_ciphertext_ballots(
            cast_ballots,
            f'verifying the ciphertext of the {n_cast} cast ballots:',
            manifest, context
        )
    except:
        all_ballots_loaded = False
        finished_verifying = False

    try:
        (spoiled_ballots, spoiled_ballot_ids, n_spoiled) = verify_load_ballots(
            public_dir, load_spoiled_ballots, errors, 'spoiled_ballots'
        )
        spoiled_ballots_loaded = True
        errors['spoiled_ballots'] = verify_ciphertext_ballots(
            spoiled_ballots,
            f'verifying the ciphertext of the {n_spoiled} spoiled ballots:',
            manifest, context
        )

    except:
        all_ballots_loaded = False
        finished_verifying = False

    if not all_ballots_loaded:
        print('Had to abort the verification.')
        summarize_errors(errors)
        return

    else:
        print('verifying that all ballots are accounted for:')

        verify_predicate(
            n_cast + n_spoiled == n_submitted,
            f'  {n_cast} ballots cast + {n_spoiled} spoiled = {n_submitted} submitted',
            errors, 'ballots_accounted_for'
        )

        verify_predicate(
            cast_ballot_ids.union(spoiled_ballot_ids) == submitted_ballot_ids,
            '  set(cast IDs) + set(spoiled IDs) = set(submitted IDs)',
            errors, 'ballots_accounted_for'
        )

    # TODO spoiled ballot decryption
    # TODO tally decryption
    # TODO aggregation

# TODO pass cfg here
def summarize_errors(errors):
    errors = {k:v for (k,v) in errors.items() if len(v) > 0}
    n_errors = sum(len(v) for v in errors.values())
    if n_errors > 0:
        print(f'ERROR Found {n_errors} irregularities...\n')
        print_colorful_json_obj(errors)
        print('The election should NOT be certified!')
        # TODO exit 1 here?


### cli ###

@click.command("verify")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def VerifyCommand(
    public_dir: str
) -> None:
    """Verify all public election artifacts.
    """
    # TODO parse and pass cfg here
    verify_election(public_dir)


@click.group
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()
