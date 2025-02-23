#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from the election admin's point of view.

from utils import (
    build_election,
    load_cast_ballots,
    load_guardian_decryption_shares,
    load_guardian_pubkeys,
    load_spoiled_ballots,
    to_public_record,
    from_public_record,
)

import click
import json
from os import listdir, makedirs
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
from electionguard import serialize
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


MANIFEST_NAME  = '1_manifest'
JOINT_KEY_NAME = 'joint_key'


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
    # print(json.dumps(locals()))

    # set up dirs
    announce_dir = join(public_dir, '1_announce')
    makedirs(public_dir, exist_ok=True)
    makedirs(announce_dir, exist_ok=True)

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
            "object_id": "referendum-pineapple", # TODO is having a number important?
            "sequence_order": 0,
            "electoral_district_id": county_id,
            "vote_variation": "one_of_m",
            "number_elected": 1,
            "votes_allowed": 1,
            "name": contest_name,
            "ballot_selections": [
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
    This is a provisional thing based on the electionguard_gui key_ceremony_service.py;
    I think eventually what we want is for everything to flow from the manifest instead.
    """
    # print(json.dumps(locals()))

    # TODO remove this entire step? not sure it adds anything
    # TODO wait actually the n guardians and quorum aren't in the manifest

    announce_dir = join(public_dir, '1_announce')
    makedirs(announce_dir, exist_ok=True)

    # based on electionguard-python/src/electionguard_gui/models/key_ceremony_service:create
    # announcement = {
    #     "created_at": datetime.utcnow(),
    #     "guardian_count": guardian_count,
    #     "quorum": guardian_quorum, # TODO guardian_quorum here too for consistency?
    #     # "backups": [],
    #     # "completed_at": None,
    #     # "created_by": self._auth_service.get_user_id(),
    #     # "guardians_joined": [],
    #     # "guardians_keys": [],
    #     # "joint_key": None,
    #     # "key_ceremony_name": key_ceremony_name,
    #     # "keys": [],
    #     # "other_keys": [],
    #     # "shared_backups": [],
    #     # "verifications": [],
    # }
    # announcement_name = '2_ceremony'
    # serialize.to_file(announcement, announcement_name, announce_dir)

    details_name = '2_ceremony'
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

    ceremony_dir = join(public_dir, '2_ceremony')
    setup_dir    = join(public_dir, '3_election')
    pubkeys_dir  = join(ceremony_dir, '1_pubkeys')
    makedirs(pubkeys_dir, exist_ok=True)
    makedirs(setup_dir, exist_ok=True)

    guardian_public_keys: List[ElectionPublicKey] = load_guardian_pubkeys(pubkeys_dir)

    election_joint_key = combine_election_public_keys(guardian_public_keys)
    assert election_joint_key is not None

    # NOTE we skip 4 to leave room for the challenge step
    to_public_record(public_dir, 'joint_key', election_joint_key)


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
    # print(json.dumps(locals()))

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

    # TODO any reason to save this when it can't be reloaded?
    # serialize.to_file(internal_manifest, 'internal_manifest', setup_dir)


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

    # set up dirs
    announce_dir  = join(public_dir, '1_announce')
    setup_dir     = join(public_dir, '3_election')
    ballots_dir   = join(public_dir, '5_ballots')
    submitted_dir = join(ballots_dir       , '1_submitted')
    cast_dir      = join(ballots_dir       , '2_cast')
    spoiled_dir   = join(ballots_dir       , '3_spoiled')

    # load required info
    manifest_path = join(announce_dir, MANIFEST_NAME + '.json')
    manifest = serialize.from_file(Manifest, manifest_path)
    joint_key_path = join(setup_dir, JOINT_KEY_NAME + '.json')
    joint_key = serialize.from_file(ElectionJointKey, joint_key_path)
    details_path = join(announce_dir, '2_ceremony.json')
    details = serialize.from_file(CeremonyDetails, details_path)
    (constants, internal_manifest, context) = build_election(
        details,
        manifest,
        joint_key
    )

    tally_name = '6_tally'
    tally_path = join(public_dir, tally_name)
    tally = CiphertextTally(
        tally_name, # TODO is this the object_id? weird
        internal_manifest,
        context
    )

    cast_ballots    = load_cast_ballots(submitted_dir, cast_dir)
    spoiled_ballots = load_spoiled_ballots(submitted_dir, spoiled_dir)

    for ballot in cast_ballots + spoiled_ballots:
        assert(tally.append(ballot, should_validate=True))

    assert tally.cast() == len(cast_ballots)
    assert tally.spoiled() == len(spoiled_ballots)
    assert tally.cast() + tally.spoiled() == len(listdir(submitted_dir))

    serialize.to_file(tally.publish(), tally_name, public_dir)


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
    # print(json.dumps(locals()))

    # set up dirs
    ceremony_dir = join(public_dir, '2_ceremony')
    pubkeys_dir  = join(ceremony_dir, '1_pubkeys')
    announce_dir  = join(public_dir, '1_announce')
    setup_dir     = join(public_dir, '3_election')
    ballots_dir   = join(public_dir, '5_ballots')
    submitted_dir = join(ballots_dir       , '1_submitted')
    cast_dir      = join(ballots_dir       , '2_cast')
    spoiled_dir   = join(ballots_dir       , '3_spoiled')
    decrypt_dir   = join(public_dir, '7_decrypt')
    shares_dir    = join(decrypt_dir       , '1_shares')
    tally_dir     = join(shares_dir        , '1_tally')
    results_dir   = join(decrypt_dir, '2_final')
    spoiled_shares_dir  = join(shares_dir , '2_spoiled')
    spoiled_results_dir = join(results_dir, '2_spoiled')
    makedirs(spoiled_results_dir, exist_ok=True)

    # load required info
    # TODO make a function if it turns out to be the proper way
    manifest_path = join(announce_dir, MANIFEST_NAME + '.json')
    manifest = serialize.from_file(Manifest, manifest_path)
    joint_key_path = join(setup_dir, JOINT_KEY_NAME + '.json')
    joint_key = serialize.from_file(ElectionJointKey, joint_key_path)
    details_path = join(announce_dir, '2_ceremony.json')
    details = serialize.from_file(CeremonyDetails, details_path)
    (constants, _, context) = build_election(
        details,
        manifest,
        joint_key
    )

    # load and decrypt tally
    tally_path = join(public_dir, '6_tally.json')
    tally_enc = serialize.from_file(PublishedCiphertextTally, tally_path)
    tally_prefix = join(tally_dir, 'tally')
    tally_shares: Dict[GuardianId, DecryptionShare] \
        = load_guardian_decryption_shares(tally_prefix, details.number_of_guardians)
    tally_result = decrypt_tally(
        tally_enc,
        tally_shares,
        context.crypto_extended_base_hash,
        manifest
    )
    assert tally_result is not None
    serialize.to_file(tally_result, '1_tally', results_dir)
    print('decrypted tally')

    # load spoiled ballots
    spoiled_ballots: List[SubmittedBallot] = load_spoiled_ballots(submitted_dir, spoiled_dir)

    # load spoiled ballot shares
    spoiled_ids = [b.object_id for b in spoiled_ballots]
    spoiled_prefixes = [join(spoiled_shares_dir, i) for i in spoiled_ids]
    spoiled_shares: Dict[str, Dict[GuardianId, DecryptionShare]] = {}
    for (bid, prefix) in zip(spoiled_ids, spoiled_prefixes):
        shares = load_guardian_decryption_shares(prefix, details.number_of_guardians)
        spoiled_shares[bid] = shares

    # decrypt spoiled ballots
    for spoiled_ballot in spoiled_ballots:
        ballot_id = spoiled_ballot.object_id
        shares: Dict[GuardianId, DecryptionShare] = spoiled_shares[ballot_id]
        spoiled_result = decrypt_ballot(
            spoiled_ballot,
            shares,
            context.crypto_extended_base_hash,
            manifest
        )
        assert spoiled_result is not None
        serialize.to_file(spoiled_result, ballot_id, spoiled_results_dir)
        print(f'decrypted {ballot_id}')


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
    Save and print a human-readable summary of the election.
    This isn't part of the ElectionGuard protocol; I just thought it would be helpful.
    """

    # set up dirs
    announce_dir = join(public_dir, '1_announce')
    decrypt_dir   = join(public_dir, '7_decrypt')
    results_dir   = join(decrypt_dir, '2_final')
    spoiled_results_dir = join(results_dir, '2_spoiled')

    # load manifest
    manifest_path = join(announce_dir, MANIFEST_NAME + '.json')
    manifest = serialize.from_file(Manifest, manifest_path)

    # load tally
    tally_result_path = join(results_dir, '1_tally.json')
    plaintext_tally = serialize.from_file(PlaintextTally, tally_result_path)

    # based on print_results_step in electionguard_cli

    csb = CliStepBase() # TODO call this "printer" or "formatter"?
    selection_names = manifest.get_selection_names("en")
    contest_names = manifest.get_contest_names()

    # summary json in my own temporary format
    summary = {
        'tally of cast ballots': [],
        'individual spoiled ballots': {},
    }

    # spoiled ballots
    spoiled_paths: Dict[BallotId, str] = {
        splitext(n)[0]: join(spoiled_results_dir, n)
        for n in listdir(spoiled_results_dir)
    }
    plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally] = {
        bid: serialize.from_file(PlaintextTally, p)
        for (bid, p) in spoiled_paths.items()
    }
    ballot_ids = plaintext_spoiled_ballots.keys()
    for ballot_id in ballot_ids:
        short_id = ballot_id[ballot_id.find('-')+1:]
        csb.print_header(f"Spoiled ballot '{short_id}'")
        spoiled_ballot = plaintext_spoiled_ballots[ballot_id]
        ballot_summary = []
        for contest in spoiled_ballot.contests.values():
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
            csb.print_section(f'{question} {answer}')
            contest_summary = {question: answer}
            ballot_summary.append(contest_summary)
        summary['individual spoiled ballots'][short_id] = ballot_summary

    # main tally
    csb.print_header("Final tally of all cast ballots")
    contest_summaries = []
    for tally_contest in plaintext_tally.contests.values():
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
        summary['tally of cast ballots'].append(contest_summary)

    serialize.to_file(summary, '8_summary', public_dir)


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
