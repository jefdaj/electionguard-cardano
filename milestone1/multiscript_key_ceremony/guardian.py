#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
#
# This script is written from a guardian's point of view.

import click
import json
from os.path import join

from electionguard.key_ceremony import (
    ElectionKeyPair,
    generate_election_key_pair,
)

def round1(guardian_id, sequence_order, quorum, guardian_keys_dir):

    # TODO how should this be saved to disk for the guardian to access in future rounds?
    # TODO maybe a PrivateGuardianRecord?
    election_key_pair: ElectionKeyPair = generate_election_key_pair(guardian_id, sequence_order, quorum)
    print('generated key pair, but not sure how to save it')

    # with open(guardian_key_pair_path, 'w') as f:
    #     json.dump(election_key_pair, f)
    # print(election_key_pair)
    # key2 = election_key_pair.share()
    # print(key2)

    # guardian_key_pair_path = join(guardian_keys_dir, guardian_id + '.json')
    # with open(guardian_key_pair_path, 'w') as f:
    #     f.write(

@click.command("key-ceremony")
@click.option(
    "--guardian-count",
    prompt="Number of guardians",
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
    "--guardian-keys-dir",
    prompt="Private guardian keys directory",
    help="The location of a directory into which will be placed the guardian's private keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--guardian-id",
    prompt="Unique ID for this guardian",
    help="Unique ID for this guardian in the ceremony",
    type=click.STRING,
)
@click.option(
    "--guardian-sequence-order",
    prompt="Sequence order for this guardian",
    help="Sequence order for this guardian in the ceremony",
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
    guardian_keys_dir: str,
    guardian_id: str,
    guardian_sequence_order: int,
    current_round: int,
) -> None:
    """
    This command runs one round of the key ceremony from the perspective of a
    particular guardian.
    """
    print(json.dumps(locals()))
    if current_round == 1:
        round1(guardian_id, guardian_sequence_order, quorum, guardian_keys_dir)
    else:
        raise Exception(f'Invalid current_round "{current_round}"')
    # with open(join(guardian_keys_dir, 'test_' + str(guardian_sequence_order) + '.txt'), 'w') as f:
    #     f.write('testing')

@click.group()
def cli() -> None:
    pass

cli.add_command(GuardianKeyCeremonyCommand)

if __name__ == '__main__':
    cli()
