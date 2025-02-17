#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from the election admin's point of view.

import click
import json
from pprint import pprint
from os import makedirs
from os.path import join
from typing import List
from datetime import datetime, timedelta

from electionguard.key_ceremony import (
    combine_election_public_keys,
    ElectionPublicKey,
    ElectionJointKey,
)
from electionguard import serialize
from electionguard.election import CiphertextElectionContext
from electionguard.constants import ElectionConstants, get_constants
from electionguard.utils import get_optional

# TODO use election_builder_step as example instead
# from electionguard.election_builder import ElectionBuilder
from electionguard_tools.helpers.election_builder import ElectionBuilder

from electionguard.manifest import Manifest, InternalManifest

from guardian import load_guardian_pubkeys


MANIFEST_NAME  = '1_manifest'
JOINT_KEY_NAME = '5_joint_key'


@click.command("build-manifest")
@click.option(
    "--public-records-dir",
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
    public_records_dir: str,
    referendum_question: str
) -> None:
    """Build a minimal valid manifest.
    For now it handles only one referendum-style yes or no question,
    provided by the user.
    """
    # print(json.dumps(locals()))

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
            "name": "ElectionGuard + Cardano County",
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
                "object_id": "referendum-question-affirmative",
                "name": {
                    "text": []
                },
                "party_id": None,
                "image_uri": None,
                "is_write_in": None
            },
            {
                "object_id": "referendum-question-negative",
                "name": {
                    "text": []
                },
                "party_id": None,
                "image_uri": None,
                "is_write_in": None
            }
        ],
        "contests": [{
            "object_id": "referendum-question",
            "sequence_order": 0,
            "electoral_district_id": county_id,
            "vote_variation": "one_of_m",
            "number_elected": 1,
            "votes_allowed": 1,
            "name": contest_name,
            "ballot_selections": [
                {
                    "object_id": "referendum-question-affirmative-selection",
                    "sequence_order": 0,
                    "candidate_id": "referendum-question-affirmative"
                },
                {
                    "object_id": "referendum-question-negative-selection",
                    "sequence_order": 1,
                    "candidate_id": "referendum-question-negative"
                }
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

    serialize.to_file(manifest, MANIFEST_NAME, public_records_dir)


@click.command("announce-key-ceremony")
@click.option(
    "--public-records-dir",
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
    "--quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
def AnnounceKeyCeremonyCommand(
    guardian_count: int,
    quorum: int,
    public_records_dir: str,
) -> None:
    """Announce key ceremony parameters.
    This is a provisional thing based on the electionguard_gui key_ceremony_service.py;
    I think eventually what we want is for everything to flow from the manifest instead.
    """
    # print(json.dumps(locals()))

    ceremony_dir = join(public_records_dir, '2_ceremony')
    makedirs(ceremony_dir, exist_ok=True)

    # based on electionguard-python/src/electionguard_gui/models/key_ceremony_service:create
    announcement = {
        "created_at": datetime.utcnow(),
        "guardian_count": guardian_count,
        "quorum": quorum,
        # "backups": [],
        # "completed_at": None,
        # "created_by": self._auth_service.get_user_id(),
        # "guardians_joined": [],
        # "guardians_keys": [],
        # "joint_key": None,
        # "key_ceremony_name": key_ceremony_name,
        # "keys": [],
        # "other_keys": [],
        # "shared_backups": [],
        # "verifications": [],
    }
    announcement_name = '0_announce'
    serialize.to_file(announcement, announcement_name, ceremony_dir)


@click.command("publish-joint-key")
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed the guardian's public keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def PublishJointKeyCommand(
    public_records_dir: str,
) -> None:
    """Final step in the key ceremony.
    Could technically be posted on chain by anyone, not just the admin.
    """
    # print(json.dumps(locals()))

    ceremony_dir = join(public_records_dir, '2_ceremony')
    pubkeys_dir = join(ceremony_dir, '1_pubkeys')
    makedirs(pubkeys_dir, exist_ok=True)

    guardian_public_keys: List[ElectionPublicKey] = load_guardian_pubkeys(pubkeys_dir)

    election_joint_key = combine_election_public_keys(guardian_public_keys)
    assert election_joint_key is not None

    # NOTE we skip 4 to leave room for the challenge step
    serialize.to_file(election_joint_key, JOINT_KEY_NAME, ceremony_dir)


@click.command("build-election")
@click.option(
    "--guardian-count",
    prompt="Number of s",
    help="The number of guardians that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def BuildElectionCommand(
    guardian_count: int,
    quorum: int,
    public_records_dir: str,
) -> None:
    """Build the InternalManifest and CiphertextElectionContext.
    """
    # print(json.dumps(locals()))

    # set up dirs
    election_dir = join(public_records_dir, '3_election')
    makedirs(election_dir, exist_ok=True)

    # load manifest
    manifest_path = join(public_records_dir, MANIFEST_NAME + '.json')
    manifest = serialize.from_file(Manifest, manifest_path)
    # pprint(manifest)

    # load joint public key
    ceremony_dir = join(public_records_dir, '2_ceremony')
    joint_key_path = join(ceremony_dir, JOINT_KEY_NAME + '.json')
    joint_key = serialize.from_file(ElectionJointKey, joint_key_path)

    election_builder = ElectionBuilder(
        guardian_count,
        quorum,
        manifest,
    )

    # TODO add this using IPFS later
    # if verification_url is not None:
    #     election_builder.add_extended_data_field(
    #         self.VERIFICATION_URL_NAME, verification_url
    #     )

    # click.echo("Creating context and internal manifest")

    # from electionguard_tools/factories/election_factory
    election_builder.set_public_key(
        get_optional(joint_key).joint_public_key
    )
    election_builder.set_commitment_hash(
        get_optional(joint_key).commitment_hash
    )

    internal_manifest: InternalManifest
    context:           CiphertextElectionContext
    constants:         ElectionConstants
    internal_manifest, context = get_optional(election_builder.build())
    constants = get_constants()

    # TODO combine these into one big json? might need guardian records first?
    #      see election_factory.py
    serialize.to_file(internal_manifest, 'internal_manifest', election_dir)
    serialize.to_file(context, 'context', election_dir)
    serialize.to_file(constants, 'constants', election_dir)


@click.group()
def cli() -> None:
    pass

cli.add_command(BuildManifestCommand)
cli.add_command(AnnounceKeyCeremonyCommand)
cli.add_command(PublishJointKeyCommand)
cli.add_command(BuildElectionCommand)

if __name__ == '__main__':
    cli()
