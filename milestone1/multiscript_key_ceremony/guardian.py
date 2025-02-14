#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from a guardian's point of view.

import click
import json

from typing import Dict
from pprint import pprint

from os import listdir
from os.path import join, splitext

from electionguard.key_ceremony import (
    ElectionKeyPair,
    generate_election_key_pair,
)
from electionguard import serialize
from electionguard.guardian import (
    GuardianRecord,
    publish_guardian_record
)

def round1(guardian_id, sequence_order, quorum, public_records_dir, private_records_dir):

    # generate election key pair
    # NOTE there will eventually also be separate a Cardano wallet key pair
    election_key_pair: ElectionKeyPair = generate_election_key_pair(guardian_id, sequence_order, quorum)
    serialize.to_file(election_key_pair, 'election_key_pair', private_records_dir)

    # share the public key (and other info)
    public_record: GuardianRecord = publish_guardian_record(election_key_pair.share())
    serialize.to_file(public_record, guardian_id, public_records_dir)


def round2(guardian_id, sequence_order, public_records_dir, private_records_dir):

    # restore own private state
    election_key_pair_path = join(private_records_dir, 'election_key_pair.json')
    election_key_pair = serialize.from_file(ElectionKeyPair, election_key_pair_path)

    # load other guardians' public keys from shared folder
    # TODO factor out as a funcion
    other_guardian_records: Dict[str, GuardianRecord] = {}
    for json_filename in listdir(public_records_dir):
        other_guardian_id = splitext(json_filename)[0]
        if other_guardian_id == guardian_id:
            continue
        json_path = join(public_records_dir, json_filename)
        other_guardian_record = serialize.from_file(GuardianRecord, json_path)
        other_guardian_records[other_guardian_id] = other_guardian_record
    # pprint(other_guardian_records)

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
