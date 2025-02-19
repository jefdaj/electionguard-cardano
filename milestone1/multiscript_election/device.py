#!/usr/bin/env python3

# Based on ???
# Instead of one script, this has one script per party and they coordinate via
# a shared folder on the local filesystem.  This script is written from the
# encryption device's point of view.

import click
import json
import uuid
from pprint import pprint
from os import makedirs, listdir
from os.path import join
from typing import List, Tuple

# from datetime import datetime, timedelta

from electionguard.key_ceremony import (
    # combine_election_public_keys,
    # ElectionPublicKey,
    ElectionJointKey,
)
from electionguard import serialize
from electionguard.election import CiphertextElectionContext
from electionguard.constants import ElectionConstants
# from electionguard.utils import get_optional
from electionguard.manifest import Manifest, InternalManifest
from electionguard.encrypt import EncryptionDevice, contest_from, generate_device_uuid

from electionguard.ballot import (
    CiphertextBallot,
    PlaintextBallot,
    PlaintextBallotSelection,
    PlaintextBallotContest,
    SubmittedBallot,
)
from electionguard.encrypt import EncryptionDevice
from electionguard.encrypt import EncryptionMediator

from admin import build_election

from electionguard.data_store import DataStore
from electionguard.ballot_box import (
    BallotBox,
    BallotBoxState,
    submit_ballot_to_box
)


MANIFEST_NAME  = '1_manifest'
JOINT_KEY_NAME = '3_jointkey'
POLLING_PLACE  = 'electionguard-cardano-polling-place'
DEVICE_PREFIX  = 'device_'


@click.command("add-device")
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def AddDeviceCommand(
    public_records_dir: str,
) -> None:
    """Add (announce?) an encryption device,
    which will encrypt + publish ballots and do the Benaloh challenge.
    """
    # print(json.dumps(locals()))
    devices_dir  = join(public_records_dir, '5_devices')
    makedirs(devices_dir, exist_ok=True)
    device = EncryptionDevice(
        generate_device_uuid(), # device id (TODO is this deterministic?)
        12345, # session id  (TODO what's this?)
        45678, # launch code (TODO what's this?)
        POLLING_PLACE,
    )
    serialize.to_file(device, DEVICE_PREFIX + str(device.device_id), devices_dir)


def load_first_device(devices_dir: str) -> EncryptionDevice:
    device_path = join(devices_dir, listdir(devices_dir)[0])
    device = serialize.from_file(EncryptionDevice, device_path)
    return device


def build_ballot(
        internal_manifest: InternalManifest,
        candidate_id: str,
    ) -> PlaintextBallot:

    ballot_id = f"ballot-{uuid.uuid1()}"
    style_id  = 'ballot-style-01'

    # TODO proper selection from contests
    candidates = [
        "referendum-question-affirmative-selection",
        "referendum-question-negative-selection"
    ]
    vote: int = candidates.index(candidate_id)
    assert vote in [0, 1]

    selections = [
        PlaintextBallotSelection(
            vote=vote,
            is_placeholder_selection=False,
            object_id=candidate_id # TODO is this right?
        )
    ]

    contests = [
        PlaintextBallotContest(
            object_id="referendum-question",
            ballot_selections=selections
        )
    ]

    ballot = PlaintextBallot(ballot_id, style_id, contests)

    return ballot


@click.command("vote")
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
@click.option(
    "--private-records-dir",
    prompt="Private records directory",
    help="The location of a directory into which will be placed the guardian's private keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--candidate-id",
    prompt="Candidate ID",
    help="The ID of the candidate to vote for. See manifest.json for valid options.",
    type=click.STRING,
)
@click.option(
    "--spoil",
    prompt="Spoil this ballot?",
    help="Whether to spoil (aka audit or challenge) this ballot.",
    type=click.BOOL,
)
def VoteCommand(
    guardian_count: int,
    quorum: int,
    public_records_dir: str,
    private_records_dir: str,
    candidate_id: str,
    spoil: bool,
) -> None:
    """Add (announce?) an encryption device,
    which will encrypt + publish ballots and do the Benaloh challenge.
    """
    # print(json.dumps(locals()))

    # set up dirs
    plaintext_dir = join(private_records_dir, 'plaintext_ballots')
    makedirs(plaintext_dir, exist_ok=True)

    ceremony_dir  = join(public_records_dir, '2_ceremony')
    election_dir  = join(public_records_dir, '4_election')
    devices_dir   = join(public_records_dir, '5_devices')
    ballots_dir   = join(public_records_dir, '6_ballots')
    submitted_dir = join(ballots_dir       , '1_submitted')
    cast_dir      = join(ballots_dir       , '2_cast')
    spoiled_dir   = join(ballots_dir       , '3_spoiled')
    makedirs(cast_dir   , exist_ok=True)
    makedirs(spoiled_dir, exist_ok=True)

    # load manifest
    # TODO factor out into a function in admin.py
    manifest_path = join(public_records_dir, MANIFEST_NAME + '.json')
    manifest = serialize.from_file(Manifest, manifest_path)

    # load joint public key
    # TODO factor out into a function in admin.py
    joint_key_path = join(public_records_dir, JOINT_KEY_NAME + '.json')
    joint_key = serialize.from_file(ElectionJointKey, joint_key_path)

    # TODO is the underscore thing OK in python?
    (_, internal_manifest, context) = build_election(guardian_count, quorum, manifest, joint_key)
    device = load_first_device(devices_dir)

    ballot: PlaintextBallot = build_ballot(internal_manifest, candidate_id)
    serialize.to_file(ballot, str(ballot.object_id), plaintext_dir)

    encrypter = EncryptionMediator(
        internal_manifest, context, device
    )

    # neither of these will be used again after this step
    store1 = DataStore() # for submitted ballots
    store2 = DataStore() # for cast + spoiled ballots

    # ballots in progress (not yet cast or spoiled)
    # WARNING don't publish the _enc version because it includes nonces
    ballot_enc: CiphertextBallot = encrypter.encrypt(ballot)
    ballot_submitted: SubmittedBallot = submit_ballot_to_box(
        ballot_enc,
        BallotBoxState.UNKNOWN,
        internal_manifest,
        context,
        store1
    )
    assert ballot_submitted.nonce is None
    serialize.to_file(ballot_submitted, str(ballot.object_id), submitted_dir)

    if spoil:
        ballot_spoiled: SubmittedBallot = submit_ballot_to_box(
            ballot_enc,
            BallotBoxState.SPOILED,
            internal_manifest,
            context,
            store2
        )
        spoiled_path = join(spoiled_dir, ballot.object_id + '.json')
        serialize.to_file(ballot_spoiled, str(ballot_spoiled.object_id), spoiled_dir)

    else:
        ballot_cast: SubmittedBallot = submit_ballot_to_box(
            ballot_enc,
            BallotBoxState.CAST,
            internal_manifest,
            context,
            store2
        )
        cast_path = join(cast_dir, ballot.object_id + '.json')
        serialize.to_file(ballot_cast, str(ballot_cast.object_id), cast_dir)



@click.group()
def cli() -> None:
    pass

cli.add_command(AddDeviceCommand)
cli.add_command(VoteCommand)

if __name__ == '__main__':
    cli()
