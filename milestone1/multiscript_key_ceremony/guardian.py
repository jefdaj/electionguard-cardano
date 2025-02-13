#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from a guardian's point of view.

import click
import json
from os.path import join

from electionguard.key_ceremony import (
    ElectionKeyPair,
    generate_election_key_pair,
)
from electionguard import serialize

def round1(guardian_id, sequence_order, quorum, public_records_dir, private_records_dir):
    election_key_pair: ElectionKeyPair = generate_election_key_pair(guardian_id, sequence_order, quorum)
    serialize.to_file(election_key_pair.share(), guardian_id, public_records_dir)
    serialize.to_file(election_key_pair, 'election_key_pair', private_records_dir)
    # TODO does each guardian also need to save the others' keys now, or does the public_record suffice?

def round2(guardian_id, sequence_order, private_records_dir):
    election_key_pair_path = join(private_records_dir, 'election_key_pair.json')
    election_key_pair = serialize.from_file(ElectionKeyPair, election_key_pair_path)
    print(election_key_pair)

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
        # TODO write this next
        round2(guardian_id, guardian_sequence_order, private_records_dir)
    else:
        raise Exception(f'Invalid current_round "{current_round}"')

@click.group()
def cli() -> None:
    pass

cli.add_command(GuardianKeyCeremonyCommand)

if __name__ == '__main__':
    cli()
