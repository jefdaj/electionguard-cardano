#!/usr/bin/env python3

# Based on ???
# Instead of one script, this has one script per party and they coordinate via
# a shared folder on the local filesystem.  This script is written from the
# encryption device's point of view.

import click
import json
from pprint import pprint
from os import makedirs
from os.path import join
from typing import List

# from datetime import datetime, timedelta

from electionguard.key_ceremony import (
    # combine_election_public_keys,
    # ElectionPublicKey,
    ElectionJointKey,
)
from electionguard import serialize
from electionguard.election import CiphertextElectionContext
# from electionguard.constants import ElectionConstants, get_constants
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
    print(json.dumps(locals()))

    # set up dirs
    ceremony_dir = join(public_records_dir, '2_ceremony')
    election_dir = join(public_records_dir, '3_election')
    devices_dir  = join(public_records_dir, '4_devices')
    makedirs(devices_dir, exist_ok=True)

    # load internal manifest
    # can the internal manifest not be restored from file because of the hash?
    # TODO confirm with the ElectionGuard authors, and if so use my fork/patch
    internal_manifest_path = join(election_dir, 'internal_manifest.json')
    internal_manifest = serialize.from_file(InternalManifestNoPostInit, internal_manifest_path)

    # load context
    context_path = join(election_dir, 'context.json')
    context = serialize.from_file(CiphertextElectionContext, context_path)

    # raise SystemExit

    device = EncryptionDevice(
        generate_device_uuid(), # device id
        12345, # session id  (TODO what's this?)
        45678, # launch code (TODO what's this?)
        POLLING_PLACE,
    )

    serialize.to_file(device, DEVICE_PREFIX + str(device.device_id), devices_dir)

    # TODO this actually belongs in the next step, right?
    encrypter = EncryptionMediator(
        internal_manifest, context, device
    )
    # plaintext_ballots: List[PlaintextBallot]
    # ciphertext_ballots: List[CiphertextBallot] = []

@click.group()
def cli() -> None:
    pass

cli.add_command(AddDeviceCommand)

if __name__ == '__main__':
    cli()
