#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.

# This script is written from a guardian's point of view.

# def main(args):

    # public_record_dir = args[0]
    # n_guardians = int(args[1])
    # quorum = int(args[2])
    # current_round = int(args[3])

    # if current_round == 1:
        # guardian_keys_dir = os.path.join(public_record_dir, 'round_1_guardian_keys')
        # os.makedirs(guardian_keys_dir, exist_ok=True)

    # elif current_round == 2:
        # guardian_backups_dir = os.path.join(public_record_dir, 'round_2_guardian_backups')
        # os.makedirs(guardian_backups_dir, exist_ok=True)

    # elif current_round == 3:
        # guardian_verifications_dir = os.path.join(public_record_dir, 'round_3_guardian_verifications')
        # os.makedirs(guardian_verifications_dir, exist_ok=True)

    # else:
        # raise Exception(f'invalid current_round "{current_round}"')

# if __name__ == '__main__':
    # main(sys.argv[1:])

# @click.option(
#     "--public-record-dir",
#     prompt="Public Record Output Directory",
#     help="The location of a directory into which will be placed the public record files",
#     type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
# )

import click
import json
from os.path import join

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
    # with open(join(guardian_keys_dir, 'test_' + str(guardian_sequence_order) + '.txt'), 'w') as f:
    #     f.write('testing')

@click.group()
def cli() -> None:
    pass

cli.add_command(GuardianKeyCeremonyCommand)

if __name__ == '__main__':
    cli()
