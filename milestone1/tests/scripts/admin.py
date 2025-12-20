#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from the election admin's point of view.

from utils import (
    build_election,
    load_cast_ballots,
    load_tally_shares,
    load_spoiled_shares,
    load_spoiled_results,
    load_guardian_pubkeys,
    load_spoiled_ballots,
    to_public_record,
    from_public_record,
)

import click
import json
from os.path import join, splitext
from typing import List, Tuple
from datetime import datetime, timedelta
from pprint import pprint

from electionguard.key_ceremony import (
    combine_election_public_keys,
    ElectionPublicKey,
    ElectionJointKey,
    CeremonyDetails,
)
from electionguard.election import CiphertextElectionContext
from electionguard.constants import ElectionConstants, get_constants
from electionguard.utils import get_optional
from electionguard.tally import (
    CiphertextTally,
    PublishedCiphertextTally
)

from electionguard.ballot import (
    SubmittedBallot,
)

# TODO use election_builder_step as example instead
# from electionguard.election_builder import ElectionBuilder
from electionguard_tools.helpers.election_builder import ElectionBuilder

from electionguard.manifest import Manifest, InternalManifest

from electionguard.ballot_box import BallotBoxState

from electionguard.decrypt_with_shares import (
    decrypt_ballot,
    decrypt_tally,
)

from electionguard.decryption_mediator import DecryptionMediator

from electionguard_cli.cli_steps.cli_step_base import CliStepBase
from electionguard.tally import PlaintextTally


@click.command("build-manifest")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--referendum-question",
    prompt="Referendum style yes-or-no question",
    help="The yes-or-no question to be put to voters in this test election.",
    type=click.STRING,
)
def BuildManifestCommand(
    public_dir: str,
    referendum_question: str
) -> None:
    """Build a minimal valid manifest.
    For now it handles only one referendum-style yes or no question,
    provided by the user.
    """

    now = datetime.utcnow()
    county_id = "electionguard-cardano-test-county"
    contest_name = referendum_question

    manifest = {
        'election_scope_id': 'electionguard-cardano-test-manifest',
        'spec_version': '1.0', # TODO is this right?
        'type': 'general',
        'start_date': now,
        'end_date': now + timedelta(days=2, hours=12), # TODO does it matter?
        'geopolitical_units': [{
            "object_id": county_id,
            "name": "ElectionGuard + Cardano Test County",
            "type": "municipality",
            "contact_information": None,
        }],
        "parties": [{
            "object_id": "N/A",
            "name": {
                "text": []
            },
            "abbreviation": None,
            "color": None,
            "logo_uri": None
        }],
        "candidates": [
            {
                "object_id": "referendum-pineapple-affirmative",
                "name": {
                    "text": [{"value": "Yes", "language": "en"}]
                },
                "party_id": None,
                "image_uri": None,
                "is_write_in": None
            },
            {
                "object_id": "referendum-pineapple-negative",
                "name": {
                    "text": [{"value": "No", "language": "en"}]
                },
                "party_id": None,
                "image_uri": None,
                "is_write_in": None
            },
            {
                "object_id": "referendum-pineapple-unsure",
                "name": {
                    "text": [{"value": "Unsure", "language": "en"}]
                },
                "party_id": None,
                "image_uri": None,
                "is_write_in": None
            },
        ],
        "contests": [{
            "object_id": "referendum-pineapple",
            "sequence_order": 0,
            "electoral_district_id": county_id,
            "vote_variation": "one_of_m",
            "number_elected": 1,
            "votes_allowed": 1,
            "name": contest_name,
            "ballot_selections": [
                # TODO should sequence_order start from 0?
                {
                    "object_id": "referendum-pineapple-affirmative-selection",
                    "sequence_order": 1,
                    "candidate_id": "referendum-pineapple-affirmative"
                },
                {
                    "object_id": "referendum-pineapple-negative-selection",
                    "sequence_order": 2,
                    "candidate_id": "referendum-pineapple-negative"
                },
                {
                    "object_id": "referendum-pineapple-unsure-selection",
                    "sequence_order": 3,
                    "candidate_id": "referendum-pineapple-unsure"
                },
            ],
            "ballot_title": None,
            "ballot_subtitle": None
        }],
        "ballot_styles": [{
            "object_id": "ballot-style-01",
            "geopolitical_unit_ids": [county_id],
            "party_ids": None,
            "image_uri": None
        }],
        "name": {
            "text": [
                {
                    "value": "ElectionGuard + Cardano Test Election",
                    "language": "en"
                },
                {
                    # TODO spanish for test?
                    "value": "Eleccion del ElectionGuard + Cardano",
                    "language": "es"
                }
            ]
        },
        "contact_information": None
    }

    to_public_record(public_dir, 'manifest', manifest)


# TODO combine this step with the manifest above into "announce"?
@click.command("announce-key-ceremony")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--guardian-count",
    prompt="Number of s",
    help="The number of guardians that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--guardian-quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
def AnnounceKeyCeremonyCommand(
    guardian_count: int,
    guardian_quorum: int,
    public_dir: str,
) -> None:
    """Announce key ceremony parameters.
    This is provisional based on the electionguard_gui key_ceremony_service.py;
    I'm not sure whether it's the right approach yet.
    """

    details = CeremonyDetails(guardian_count, guardian_quorum)
    to_public_record(public_dir, 'ceremony_details', details)


@click.command("publish-joint-key")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed the guardian's public keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def PublishJointKeyCommand(
    public_dir: str,
) -> None:
    """Final step in the key ceremony.
    Could technically be posted on chain by anyone, not just the admin.
    """

    # print(json.dumps(locals()))

    guardian_public_keys: List[ElectionPublicKey] = load_guardian_pubkeys(public_dir)
    joint_key = combine_election_public_keys(guardian_public_keys)
    assert joint_key is not None
    to_public_record(public_dir, 'joint_key', joint_key)


@click.command("build-election")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def BuildElectionCommand(
    public_dir: str,
) -> None:
    """Build the InternalManifest and CiphertextElectionContext.
    """

    manifest  = from_public_record(public_dir, 'manifest')
    details   = from_public_record(public_dir, 'ceremony_details')
    joint_key = from_public_record(public_dir, 'joint_key')

    (constants, internal_manifest, context) = build_election(
        details,
        manifest,
        joint_key
    )

    to_public_record(public_dir, 'constants', constants)
    to_public_record(public_dir, 'context', context)


@click.command("tally")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def TallyCommand(
    public_dir: str,
) -> None:
    """Tally election results.
    """

    # script = __file__
    # print(json.dumps(locals()))

    details   = from_public_record(public_dir, 'ceremony_details')
    manifest  = from_public_record(public_dir, 'manifest')
    joint_key = from_public_record(public_dir, 'joint_key')
    (_, internal_manifest, context) = build_election(
        details, manifest, joint_key
    )

    tally = CiphertextTally(
        'ciphertext-tally', # TODO best practices for this object_id?
        internal_manifest,
        context
    )

    cast_ballots    = load_cast_ballots(public_dir)
    spoiled_ballots = load_spoiled_ballots(public_dir)

    for ballot in cast_ballots + spoiled_ballots:
        assert(tally.append(ballot, should_validate=True))

    assert tally.cast()    == len(cast_ballots)
    assert tally.spoiled() == len(spoiled_ballots)

    to_public_record(public_dir, 'ciphertext_tally', tally.publish())


# TODO utility functions for these repeated click options
@click.command("decrypt-results")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def DecryptResultsCommand(
    public_dir: str,
) -> None:
    """
    Combine guardian decryption shares into final results: tally + spoiled ballots.
    """

    # load common required info
    manifest  = from_public_record(public_dir, 'manifest')
    joint_key = from_public_record(public_dir, 'joint_key')
    details   = from_public_record(public_dir, 'ceremony_details')

    (constants, _, context) = build_election(
        details,
        manifest,
        joint_key
    )

    # load and decrypt tally
    # TODO separate command from spoiled ballots below?
    try:
        tally_enc = from_public_record(public_dir, 'ciphertext_tally')
        tally_shares: Dict[GuardianId, DecryptionShare] \
            = load_tally_shares(public_dir, details.number_of_guardians)
        tally_result = decrypt_tally(
            tally_enc,
            tally_shares,
            context.crypto_extended_base_hash,
            manifest
        )
        assert tally_result is not None
        to_public_record(public_dir, 'plaintext_tally', tally_result)
    except Exception as e:
        print(e)
        print('Failed to decrypt tally')

    # load and decrypt spoiled ballots
    spoiled_ballots: List[SubmittedBallot] = load_spoiled_ballots(public_dir)
    for spoiled_ballot in spoiled_ballots:
        try:
            spoiled_shares: Dict[GuardianId, DecryptionShare] = load_spoiled_shares(
                public_dir, details.number_of_guardians,
                spoiled_id=spoiled_ballot.object_id
            )
            spoiled_result = decrypt_ballot(
                spoiled_ballot,
                spoiled_shares,
                context.crypto_extended_base_hash,
                manifest
            )
            assert spoiled_result is not None
            to_public_record(
                public_dir, 'spoiled_result', spoiled_result,
                ballot_id=spoiled_result.object_id
            )
        except Exception as e:
            print(e)
            print(f'Failed to decrypt spoiled ballot {spoiled_ballot.object_id}')


@click.command("summary")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def SummaryCommand(
    public_dir: str,
) -> None:
    """
    Save and print a human-readable summary of the decrypted results.
    Roughly based on print_results_step in the electionguard_cli.
    """

    # TODO import the version from the verifier here instead once that exists

    csb = CliStepBase() # prints in electionguard_cli style

    manifest        = from_public_record(public_dir, 'manifest')
    tally_result    = from_public_record(public_dir, 'plaintext_tally')
    spoiled_results = load_spoiled_results(public_dir)

    selection_names = manifest.get_selection_names("en")
    contest_names   = manifest.get_contest_names()

    spoiled_header = 'Individual spoiled ballots'
    csb.print_header(spoiled_header)
    print()
    spoiled_summaries = {}
    for spoiled_result in spoiled_results:
        ballot_id = spoiled_result.object_id
        short_id  = ballot_id[ballot_id.find('-')+1:]
        print(short_id)
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
            print(f'  {question} {answer}')
            contest_summary = {question: answer}
            ballot_summary.append(contest_summary)
        spoiled_summaries[short_id] = ballot_summary
        print()

    tally_header = "Tally of all cast ballots"
    csb.print_header(tally_header)
    tally_summary = []
    contest_summaries = []
    for tally_contest in tally_result.contests.values():
        contest_name = contest_names.get(tally_contest.object_id)
        contest_summary = {
            'question': contest_name,
            'votes': {},
        }
        csb.print_section(contest_name)
        values = list(tally_contest.selections.values())
        values.sort(key=lambda v: v.tally, reverse=True)
        for selection in values:
            name = selection_names[selection.object_id]
            csb.print_value(f"  {name}", selection.tally)
            contest_summary['votes'][name] = selection.tally
        tally_summary.append(contest_summary)

    # save summary json
    # no particular format, except it must be a json-serializable dict
    summary = {
        tally_header  : tally_summary,
        spoiled_header: spoiled_summaries,
    }
    to_public_record(public_dir, 'summary', summary)


@click.group()
def cli() -> None:
    pass

cli.add_command(BuildManifestCommand)
cli.add_command(AnnounceKeyCeremonyCommand)
cli.add_command(PublishJointKeyCommand)
cli.add_command(BuildElectionCommand)
cli.add_command(TallyCommand)
cli.add_command(DecryptResultsCommand)
cli.add_command(SummaryCommand)

if __name__ == '__main__':
    cli()
