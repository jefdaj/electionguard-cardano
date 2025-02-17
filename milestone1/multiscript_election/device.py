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
from electionguard.manifest import InternalManifestNoPostInit
from electionguard.encrypt import EncryptionDevice, contest_from, generate_device_uuid

from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
    PlaintextBallot,
    SubmittedBallot,
)
from electionguard.encrypt import EncryptionDevice
from electionguard.encrypt import EncryptionMediator


POLLING_PLACE = 'electionguard-cardano-polling-place'
DEVICE_PREFIX = 'device_'
BALLOT_PREFIX = 'ballot_'


def load_election_info(election_dir: str) -> \
        Tuple[
            ElectionConstants,
            InternalManifestNoPostInit,
            CiphertextElectionContext
        ]:

    # load constants
    constants_path = join(election_dir, 'constants.json')
    constants = serialize.from_file(ElectionConstants, constants_path)

    # load context
    context_path = join(election_dir, 'context.json')
    context = serialize.from_file(CiphertextElectionContext, context_path)

    # load internal manifest
    # can the internal manifest not be restored from file because of the hash?
    # TODO confirm with the ElectionGuard authors, and if so use my fork/patch
    internal_manifest_path = join(election_dir, 'internal_manifest.json')
    internal_manifest = serialize.from_file(InternalManifestNoPostInit, internal_manifest_path)

    return (constants, context, internal_manifest)


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

    # set up dirs
    ceremony_dir = join(public_records_dir, '2_ceremony')
    election_dir = join(public_records_dir, '3_election')
    devices_dir  = join(public_records_dir, '4_devices')
    makedirs(devices_dir, exist_ok=True)

    # TODO is the underscore thing OK in python?
    (_, context, internal_manifest) = load_election_info(election_dir)

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
        ballots_dir: str,
        internal_manifest: InternalManifestNoPostInit,
        candidate_id: str,
        spoil: bool
    ) -> PlaintextBallot:
    ballot_id = f"ballot-{uuid.uuid1()}"
    style_id  = 'ballot-style-01'
    contests  = internal_manifest.contests
    pprint(contests)
    # contests[0].valid = True # TODO is this a bad idea?
    ballot = PlaintextBallot(ballot_id, style_id, contests)
    # TODO finish this
    return ballot


@click.command("vote")
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
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
    public_records_dir: str,
    candidate_id: str,
    spoil: bool,
) -> None:
    """Add (announce?) an encryption device,
    which will encrypt + publish ballots and do the Benaloh challenge.
    """
    print(json.dumps(locals()))

    # set up dirs
    ceremony_dir = join(public_records_dir, '2_ceremony')
    election_dir = join(public_records_dir, '3_election')
    devices_dir  = join(public_records_dir, '4_devices')
    ballots_dir  = join(public_records_dir, '5_ballots')
    makedirs(ballots_dir, exist_ok=True)

    (_, context, internal_manifest) = load_election_info(election_dir)
    device = load_first_device(devices_dir)

    # TODO this actually belongs in the next step, right?
    encrypter = EncryptionMediator(
        internal_manifest, context, device
    )

    ballot:     PlaintextBallot  = build_ballot(ballots_dir, internal_manifest, candidate_id, spoil)
    ballot_enc: CiphertextBallot = encrypter.encrypt(ballot)

    serialize.to_file(ballot_enc, BALLOT_PREFIX + str(ballot.object_id), ballots_dir)


@click.group()
def cli() -> None:
    pass

cli.add_command(AddDeviceCommand)
cli.add_command(VoteCommand)

if __name__ == '__main__':
    cli()
