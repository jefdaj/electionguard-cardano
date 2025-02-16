#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from the election admin's point of view.

import click
import json
from pprint import pprint
from os.path import join
from typing import List

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
    help="The location of a directory into which will be placed the guardian's public keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def AnnounceKeyCeremonyCommand(
    public_records_dir: str,
) -> None:
    """Final step in the key ceremony.
    Could technically be posted on chain by anyone, not just the admin.
    """
    print(json.dumps(locals()))

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
