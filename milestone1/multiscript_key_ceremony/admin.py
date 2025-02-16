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
from datetime import datetime

from electionguard.key_ceremony import (
    combine_election_public_keys,
    ElectionPublicKey,
)
from electionguard import serialize

from guardian import load_guardian_pubkeys


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
    print(json.dumps(locals()))

    makedirs(public_records_dir, exist_ok=True)

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
    serialize.to_file(announcement, announcement_name, public_records_dir)


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
    print(json.dumps(locals()))

    # TODO remove? should never be needed
    makedirs(public_records_dir, exist_ok=True)

    pubkeys_dir = join(public_records_dir, '1_guardian_pubkeys')
    guardian_public_keys: List[ElectionPublicKey] = load_guardian_pubkeys(pubkeys_dir)

    election_joint_key = combine_election_public_keys(guardian_public_keys)
    assert election_joint_key is not None

    # NOTE we skip 4 to leave room for the challenge step
    joint_key_name = '5_joint_key'
    serialize.to_file(election_joint_key, joint_key_name, public_records_dir)


@click.group()
def cli() -> None:
    pass

cli.add_command(PublishJointKeyCommand)
cli.add_command(AnnounceKeyCeremonyCommand)

if __name__ == '__main__':
    cli()
