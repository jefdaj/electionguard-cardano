#!/usr/bin/env python3

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
from datetime import datetime
from dataclasses import dataclass

from electionguard.key_ceremony import (
    # combine_election_public_keys,
    # ElectionPublicKey,
    ElectionJointKey,
    CeremonyDetails,
)

from electionguard import serialize
from electionguard.election import CiphertextElectionContext
from electionguard.constants import ElectionConstants
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

from utils import (
    build_ballot,
    build_election,
    load_designated_backups,
    load_device_by_number,
    to_public_record,
    from_public_record,
)


MANIFEST_NAME  = '1_manifest'
JOINT_KEY_NAME = 'joint_key'
POLLING_PLACE  = 'electionguard-cardano-polling-place'
# DEVICE_PREFIX  = 'device_'


@click.command("add-device")
@click.option(
    "--device-number",
    prompt="Device number",
    help="The number of the device.",
    type=click.INT,
)
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def AddDeviceCommand(
    device_number: int,
    public_dir: str,
) -> None:
    """Add (announce?) an encryption device,
    which will encrypt + publish ballots and do the Benaloh challenge.
    """
    # print(json.dumps(locals()))
    devices_dir  = join(public_dir, '4_devices')
    makedirs(devices_dir, exist_ok=True)
    device = EncryptionDevice(
        generate_device_uuid(), # device id (TODO is this deterministic?)
        device_number * 12345, # session id  (TODO what's this?)
        device_number * 45678, # launch code (TODO what's this?)
        POLLING_PLACE,
    )
    to_public_record(public_dir, 'device', device)


# TODO what should this inherit from... ElectionObjectBase? CryptoHashCheckable?
@dataclass
class CastBallotNotice(object):
    ballot_id: str
    cast_at: datetime



@click.command("vote")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--private-dir",
    prompt="Private records directory",
    help="The location of a directory into which will be placed the guardian's private keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--device-number",
    prompt="Device number",
    help="The number of the device.",
    type=click.INT,
)
@click.option(
    "--candidate",
    prompt="Candidate name",
    help="The ID of the candidate (or answer!) to vote for. See manifest.json for valid options.",
    type=click.STRING,
)
@click.option(
    "--spoil",
    prompt="Spoil this ballot?",
    help="Whether to spoil (aka audit or challenge) this ballot.",
    type=click.BOOL,
)
def VoteCommand(
    public_dir: str,
    private_dir: str,
    device_number: int,
    candidate: str,
    spoil: bool,
) -> None:
    """Add (announce?) an encryption device,
    which will encrypt + publish ballots and do the Benaloh challenge.
    """
    # print(json.dumps(locals()))

    # set up dirs
    plaintext_dir = join(private_dir, 'plaintext_ballots')
    makedirs(plaintext_dir, exist_ok=True)

    announce_dir  = join(public_dir, '1_announce')
    setup_dir     = join(public_dir, '3_election')
    devices_dir   = join(public_dir, '4_devices')
    ballots_dir   = join(public_dir, '5_ballots')
    submitted_dir = join(ballots_dir       , '1_submitted')
    cast_dir      = join(ballots_dir       , '2_cast')
    spoiled_dir   = join(ballots_dir       , '3_spoiled')
    makedirs(cast_dir   , exist_ok=True)
    makedirs(spoiled_dir, exist_ok=True)

    manifest  = from_public_record(public_dir, 'manifest')
    joint_key = from_public_record(public_dir, 'joint_key')
    details   = from_public_record(public_dir, 'ceremony_details')

    # TODO is the underscore thing OK in python?
    (_, internal_manifest, context) = build_election(details, manifest, joint_key)
    device = load_device_by_number(devices_dir, device_number)

    ballot: PlaintextBallot = build_ballot(manifest, candidate)
    serialize.to_file(ballot, str(ballot.object_id), plaintext_dir)

    encrypter = EncryptionMediator(
        internal_manifest, context, device
    )

    # neither of these will be used again after this step
    store1 = DataStore() # for submitted ballots
    store2 = DataStore() # for cast + spoiled ballots

    # ballots in progress (not yet cast or spoiled)
    # This is also used below as the "spoiled" ballot, because it includes nonces.
    ballot_enc: CiphertextBallot = encrypter.encrypt(ballot)

    # This is the same as the cast version; no need to include the files twice.
    ballot_submitted: SubmittedBallot = submit_ballot_to_box(
        ballot_enc,
        BallotBoxState.UNKNOWN,
        internal_manifest,
        context,
        store1
    )
    assert ballot_submitted.nonce is None
    to_public_record(public_dir, 'ballot_submitted', ballot_submitted)

    if spoil:

        # I think this is how the authors intended for ballots to be spoiled,
        # but it doesn't work for our purposes because they don't include the nonces!
        # They just mark the state as SPOILED but otherwise it stays the same.
        # ballot_spoiled: SubmittedBallot = submit_ballot_to_box(
        #     ballot_enc,
        #     BallotBoxState.SPOILED,
        #     internal_manifest,
        #     context,
        #     store2
        # )

        # Instead, I think we either need to publish the entire ciphertext or
        # just the master nonce. Doing the ciphertext for now.
        # TODO which would make more sense? ask around
        # TODO if using the nonce, which one specifically? nonce_seed?
        ballot_spoiled = ballot_enc
        ballot_spoiled.state = BallotBoxState.SPOILED

        to_public_record(public_dir, 'ballot_spoiled', ballot_spoiled)

    else:

        # I think this is how the authors intended for ballots to be cast,
        # but I don't see any point including the whole ballot again just to
        # change the state from UNKNOWN -> CAST.
        # ballot_cast: SubmittedBallot = submit_ballot_to_box(
        #     ballot_enc,
        #     BallotBoxState.CAST,
        #     internal_manifest,
        #     context,
        #     store2
        # )

        # Instead, we just save a placeholder json file that says "cast" and
        # would be signed by the device on chain. And eventually maybe the
        # voter's phone app too!
        cast_notice = CastBallotNotice(
            ballot_id=ballot_enc.object_id,
            cast_at=datetime.utcnow()
        )

        cast_path = join(cast_dir, ballot.object_id + '.json')
        to_public_record(public_dir, 'cast_notice', cast_notice)



@click.group()
def cli() -> None:
    pass

cli.add_command(AddDeviceCommand)
cli.add_command(VoteCommand)

if __name__ == '__main__':
    cli()
