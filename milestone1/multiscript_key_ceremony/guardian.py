#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from a guardian's point of view.

import click
import json

from os import listdir, makedirs
from os.path import join, splitext
from pprint import pprint
from typing import List, Dict

from electionguard import serialize
from electionguard.type import GuardianId
from electionguard.key_ceremony import (
    ElectionKeyPair,
    ElectionPublicKey,
    generate_election_key_pair,
    generate_election_partial_key_backup,
)


def round1(guardian_id, sequence_order, quorum, public_records_dir, private_records_dir):

    pubkeys_dir = join(public_records_dir, 'guardian_pubkeys')
    makedirs(pubkeys_dir, exist_ok=True)

    # generate election key pair
    # NOTE there will eventually also be separate a Cardano wallet key pair
    election_key_pair: ElectionKeyPair = generate_election_key_pair(guardian_id, sequence_order, quorum)
    serialize.to_file(election_key_pair, guardian_id, private_records_dir)

    # share the public key (and other info)
    # TODO why not publish_guardian_record here? I guess that's later after backups?
    public_key: ElectionPublicKey = election_key_pair.share()
    serialize.to_file(public_key, guardian_id, pubkeys_dir)


def load_guardian_pubkeys(public_records_dir: str) -> List[ElectionPublicKey]:
    guardian_pubkeys: List[ElectionPublicKey] = []
    for json_filename in listdir(public_records_dir):
        guardian_id: GuardianId = splitext(json_filename)[0]
        json_path = join(public_records_dir, json_filename)
        guardian_pubkey = serialize.from_file(ElectionPublicKey, json_path)
        guardian_pubkeys.append(guardian_pubkey)
    return guardian_pubkeys


def round2(guardian_id, sequence_order, public_records_dir, private_records_dir):

    pubkeys_dir = join(public_records_dir, 'guardian_pubkeys')
    backups_dir = join(public_records_dir, 'guardian_backups')
    makedirs(pubkeys_dir, exist_ok=True)
    makedirs(backups_dir, exist_ok=True)

    # restore own private state
    election_key_pair_path = join(private_records_dir, f'{guardian_id}.json')
    election_key_pair = serialize.from_file(ElectionKeyPair, election_key_pair_path)

    # load other guardians' public keys from shared folder
    other_guardian_pubkeys = [
        k for k in load_guardian_pubkeys(pubkeys_dir)
        if k.owner_id != guardian_id # remove self
    ]

    # save partial backups in shared folder, encrypted to each other guardians' pubkeys
    # NOTE these will be public and on-chain in my version, unless that's bad?
    for other_guardian_pubkey in other_guardian_pubkeys:
        backup = generate_election_partial_key_backup(
            guardian_id,
            election_key_pair.polynomial,
            other_guardian_pubkey,
        )
        backup_order = other_guardian_pubkey.sequence_order
        backup_name = f'{guardian_id}_backup_{backup_order}'
        serialize.to_file(backup, backup_name, backups_dir)
 

@click.command("key-ceremony")
@click.option(
    "--guardian-count",
    prompt="Number of s",
    help="The number of s that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--quorum",
    prompt="Quorum",
    help="The minimum number of s required to show up to the tally.",
    type=click.INT,
)
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed the guardian's public keys "
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
    "--guardian-id",
    prompt="Unique ID for this ",
    help="Unique ID for this  in the ceremony",
    type=click.STRING,
)
@click.option(
    "--guardian-sequence-order",
    prompt="Sequence order for this ",
    help="Sequence order for this  in the ceremony",
    type=click.INT,
)
@click.option(
    "--current-round",
    prompt="Current key ceremony round",
    help="Current key ceremony round",
    type=click.INT,
)
def GuardianKeyCeremonyCommand(
    guardian_count: int,
    quorum: int,
    public_records_dir: str,
    private_records_dir: str,
    guardian_id: str,
    guardian_sequence_order: int,
    current_round: int,
) -> None:
    """
    This command runs one round of the key ceremony from the perspective of a
    particular .
    """
    print(json.dumps(locals()))
    if current_round == 1:
        round1(guardian_id, guardian_sequence_order, quorum, public_records_dir, private_records_dir)
    elif current_round == 2:
        round2(guardian_id, guardian_sequence_order, public_records_dir, private_records_dir)
    else:
        raise Exception(f'Invalid current_round "{current_round}"')

@click.group()
def cli() -> None:
    pass

cli.add_command(GuardianKeyCeremonyCommand)

if __name__ == '__main__':
    cli()
