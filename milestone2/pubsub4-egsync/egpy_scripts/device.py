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
    to_public_record,
    to_private_record,
    from_private_record,
    from_public_record,
)


MANIFEST_NAME  = '1_manifest'
JOINT_KEY_NAME = 'joint_key'
POLLING_PLACE  = 'electionguard-cardano-polling-place'
# DEVICE_PREFIX  = 'device_'


# TODO what should this inherit from... ElectionObjectBase? CryptoHashCheckable?
@dataclass
class CastBallotNotice(object):
    ballot_id: str
    cast_at: datetime


def add_device(device_number, egsync_api):
    device = EncryptionDevice(
        generate_device_uuid(), # device id (TODO is this deterministic?)
        device_number * 12345, # session id  (TODO what's this?)
        device_number * 45678, # launch code (TODO what's this?)
        POLLING_PLACE,
    )
    device_id = 'device_' + str(device_number)
    to_public_record(egsync_api, device_id, 'device', device, device_number=device_number)

def vote_commit(egsync_api, private_dir, device_number, candidate):

    manifest  = from_public_record(egsync_api, 'manifest')
    joint_key = from_public_record(egsync_api, 'joint_key')
    details   = from_public_record(egsync_api, 'ceremony_details')

    # TODO is the underscore thing OK in python?
    (_, internal_manifest, context) = build_election(details, manifest, joint_key)
    device = from_public_record(egsync_api, 'device', device_number=device_number)

    plaintext_ballot: PlaintextBallot = build_ballot(manifest, candidate)
    to_private_record(
        private_dir, 'plaintext_ballot', plaintext_ballot,
        ballot_id=plaintext_ballot.object_id
    )

    encrypter = EncryptionMediator(
        internal_manifest, context, device
    )

    # will not be used again after this step
    store = DataStore()

    # ballots in progress (not yet cast or spoiled)
    # This is also used below as the "spoiled" ballot, because it includes nonces.
    ciphertext_ballot: CiphertextBallot = encrypter.encrypt(plaintext_ballot)

    # This is the same as the cast version; no need to include the files twice.
    ballot_submitted: SubmittedBallot = submit_ballot_to_box(
        ciphertext_ballot,
        BallotBoxState.UNKNOWN,
        internal_manifest,
        context,
        store
    )
    assert ballot_submitted.nonce is None
    ballot_id = ballot_submitted.object_id
    device_id = 'device_' + str(device_number)
    to_public_record(
        egsync_api, device_number, 'ballot_submitted', ballot_submitted,
        ballot_id=ballot_id
    )

    # "return" it via stdout in run_in_container
    # TODO is there a cleaner way to do this?
    print(ballot_id, flush=True)

def vote_reveal(egsync_api, private_dir, device_number, ballot_id, spoil):

    # store = DataStore() # for cast + spoiled ballots. will not be used again


    device_id = 'device_' + str(device_number)

    if spoil:

        details   = from_public_record(egsync_api, 'ceremony_details')
        manifest  = from_public_record(egsync_api, 'manifest')
        joint_key = from_public_record(egsync_api, 'joint_key')

        (_, internal_manifest, context) = build_election(details, manifest, joint_key)
        device = from_public_record(egsync_api, 'device', device_number=device_number)
 
        encrypter = EncryptionMediator(
            internal_manifest, context, device
        )

        plaintext_ballot = from_private_record(
            private_dir, 'plaintext_ballot',
            ballot_id=ballot_id,
        )

        # WARNING this includes nonces
        # TODO will they be the same nonces as the prev version though? we need that
        ciphertext_ballot: CiphertextBallot = encrypter.encrypt(plaintext_ballot)

        # I think this is how the authors intended for ballots to be spoiled,
        # but it doesn't work for our purposes because they don't include the nonces!
        # They just mark the state as SPOILED but otherwise it stays cast.
        # TODO is this what they meant by not having implemented decryption by nonce?
        # ballot_spoiled: SubmittedBallot = submit_ballot_to_box(
        #     ciphertext_ballot,
        #     BallotBoxState.SPOILED,
        #     internal_manifest,
        #     context,
        #     store
        # )

        # Instead, I think we either need to publish the entire ciphertext or
        # just the master nonce. Doing the ciphertext for now.
        # TODO which would make more sense? ask around
        # TODO if using the nonce, which one specifically? nonce_seed?
        ballot_spoiled = ciphertext_ballot
        ballot_spoiled.state = BallotBoxState.SPOILED

        to_public_record(
            egsync_api, device_id, 'ballot_spoiled', ballot_spoiled,
            ballot_id=ballot_spoiled.object_id
        )

    else:

        # I think this is how the authors intended for ballots to be cast,
        # but I don't see any point including the whole ballot again just to
        # change the state from UNKNOWN -> CAST. It seems confusing.
        # TODO include them anyway in order to make everything easy and symmetric?
        # ballot_cast: SubmittedBallot = submit_ballot_to_box(
        #     ballot_enc,
        #     BallotBoxState.CAST,
        #     internal_manifest,
        #     context,
        #     store
        # )

        # Instead, we save a placeholder json file that says "cast" and
        # would be signed by the device on chain. And eventually maybe the
        # voter's phone app too!
        # TODO should this include the encryption device?
        cast_notice = CastBallotNotice(
            # ballot_id=ballot_enc.object_id, # TODO just ballot_id here?
            ballot_id=ballot_id,
            cast_at=datetime.utcnow()
        )

        device_id = 'device_' + str(device_number)

        to_public_record(
            egsync_api, device_id, 'cast_notice', cast_notice,
            ballot_id=cast_notice.ballot_id
        )


### cli ###

@click.command("add-device")
@click.option(
    "--device-number",
    prompt="Device number",
    help="The number of the device.",
    type=click.INT,
)
@click.option(
    "--egsync-api",
    prompt="Base URL of the egsync API",
    help="The URL of the public records API. ",
    type=click.STRING,
)
def AddDeviceCommand(
    device_number: int,
    egsync_api: str,
) -> None:
    """Add (announce?) an encryption device,
    which will encrypt + publish ballots and do the Benaloh challenge.
    """
    add_device(device_number, egsync_api)

@click.command("vote_commit")
@click.option(
    "--egsync-api",
    prompt="Base URL of the egsync API",
    help="The URL of the public records API. ",
    type=click.STRING,
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
def VoteCommitCommand(
    egsync_api: str,
    private_dir: str,
    device_number: int,
    candidate: str,
) -> None:
    """Submit a ballot, but don't say whether it will be cast or spoiled yet.
    """
    vote_commit(egsync_api, private_dir, device_number, candidate)

@click.command("vote_reveal")
@click.option(
    "--egsync-api",
    prompt="Base URL of the egsync API",
    help="The URL of the public records API. ",
    type=click.STRING,
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
    "--ballot-id",
    prompt="Ballot ID",
    help="The ID of the ballot to reveal (cast or spoil).",
    type=click.STRING,
)
@click.option(
    "--spoil",
    prompt="Spoil this ballot?",
    help="Whether to spoil (aka audit or challenge) this ballot.",
    type=click.BOOL,
)
def VoteRevealCommand(
    egsync_api: str,
    private_dir: str,
    device_number: int,
    ballot_id: str,
    spoil: bool,
) -> None:
    """Cast or spoil a previously submitted ballot by ID.
    """
    vote_reveal(egsync_api, private_dir, device_number, ballot_id, spoil)

@click.group()
def cli() -> None:
    pass

cli.add_command(AddDeviceCommand)
cli.add_command(VoteCommitCommand)
cli.add_command(VoteRevealCommand)

if __name__ == '__main__':
    cli()
