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


### cli ###

def print_colorful_json_obj(obj):
	# based on https://stackoverflow.com/a/32166163
	formatted_json = json.dumps(obj, indent=2)
	colorful_json = highlight(
		formatted_json,
		lexers.JsonLexer(),
		formatters.TerminalFormatter()
	)
	print(colorful_json)

def verify_ciphertext_ballots(ballots, header_msg, manifest, context) -> int:
    print(header_msg)
    irregularities = {}
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
                irregularities[ballot.object_id] = ' '.join(msgs)
    print()
    return irregularities


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

    manifest  = from_public_record(public_dir, 'manifest')
    details   = from_public_record(public_dir, 'ceremony_details')
    joint_key = from_public_record(public_dir, 'joint_key')

    (_, _, context) = build_election(
        details,
        manifest,
        joint_key
    )

    irregularities = {}

    # TODO capture error in case a ballot is missing here and add to irregularities
    submitted_ballots = load_submitted_ballots(public_dir)
    cast_ballots      = load_cast_ballots(public_dir)
    spoiled_ballots   = load_spoiled_ballots(public_dir)

    print('verifying that all ballots are accounted for:')
    # TODO capture these assertions -> irregularities too

    submitted_ballot_ids = set(b.object_id for b in submitted_ballots)
    cast_ballot_ids      = set(b.object_id for b in cast_ballots)
    spoiled_ballot_ids   = set(b.object_id for b in spoiled_ballots)

    n_submitted = len(submitted_ballot_ids)
    n_cast      = len(cast_ballot_ids)
    n_spoiled   = len(spoiled_ballot_ids)

    print(f'  {n_cast} ballots cast + {n_spoiled} spoiled = {n_submitted} submitted...', end=' ')
    assert n_cast + n_spoiled == n_submitted
    print('ok')

    print('  set(cast IDs) + set(spoiled IDs) = set(submitted IDs)...', end=' ')
    assert cast_ballot_ids.union(spoiled_ballot_ids) == submitted_ballot_ids
    print('ok')

    print()

    irregularities['cast_ballots'] = verify_ciphertext_ballots(
        cast_ballots,
        f'verifying the ciphertext of the {n_cast} cast ballots:',
        manifest, context
    )

    irregularities['spoiled_ballots'] = verify_ciphertext_ballots(
        spoiled_ballots,
        f'verifying the ciphertext of the {n_spoiled} spoiled ballots:',
        manifest, context
    )

    # TODO spoiled ballot decryption
    # TODO tally decryption
    # TODO aggregation

    irregularities = {k:v for (k,v) in irregularities.items() if len(v) > 0}
    n_irregularities = sum(len(v) for v in irregularities.values())
    if n_irregularities > 0:
        print(f'ERROR Found {n_irregularities} irregularities...\n')
        print_colorful_json_obj(irregularities)
        print('The election should NOT be certified!')
        # TODO exit 1 here?


@click.group
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()
