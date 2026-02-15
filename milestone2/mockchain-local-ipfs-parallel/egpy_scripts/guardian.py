#!/usr/bin/env python3

# Based on the functional_key_ceremony integration test.
# Instead of one script, this has one script per party
# and they coordinate via a shared folder on the local filesystem.
# This script is written from a guardian's point of view.


from utils import (
    build_election,
    load_designated_backups,
    load_guardian_pubkeys,
    load_spoiled_ballots,
    to_public_record,
    to_private_record,
    from_public_record,
    from_private_record,
)


import click
import json

from os import listdir, makedirs
from os.path import join, splitext
# from pprint import pprint
from typing import List, Dict

from electionguard.guardian import Guardian
from electionguard.type import GuardianId
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionKeyPair,
    ElectionPublicKey,
    ElectionPartialKeyBackup,
    ElectionPartialKeyVerification,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    verify_election_partial_key_backup,
)
from electionguard.decryption import (
    compute_decryption_share,
    compute_decryption_share_for_ballot,
)
from electionguard.election import CiphertextElectionContext
from electionguard.tally import (
    CiphertextTally,
    PublishedCiphertextTally,
)
from electionguard.manifest import Manifest, InternalManifest
from electionguard.key_ceremony import (
    ElectionJointKey
)


def round1(guardian_id, sequence_order, egsync_api, private_dir):
    '''Round 1: create and share pubkeys
    '''

    details = from_public_record(egsync_api, 'ceremony_details')

    # generate election key pair
    # there will eventually also be separate a Cardano wallet key pair
    election_key_pair: ElectionKeyPair = generate_election_key_pair(
        guardian_id, sequence_order, details.quorum
    )
    to_private_record(private_dir, 'election_key_pair', election_key_pair)

    # share the public key (and other info)
    public_key: ElectionPublicKey = election_key_pair.share()
    to_public_record(
        egsync_api, guardian_id, 'guardian_pubkey', public_key,
        guardian_id=guardian_id
    )


def round2(guardian_id, sequence_order, egsync_api, private_dir):
    '''Round 2: create and share backups
    '''

    election_key_pair = from_private_record(private_dir, 'election_key_pair')

    # load other guardians' public keys from shared folder
    other_guardian_pubkeys = [
        k for k in load_guardian_pubkeys(egsync_api)
        if k.owner_id != guardian_id # remove self
    ]

    # save partial backups in shared folder,
    # encrypted to each other guardians' pubkeys
    # these will go on-chain in my version
    for other_pubkey in other_guardian_pubkeys:
        backup = generate_election_partial_key_backup(
            guardian_id,
            election_key_pair.polynomial,
            other_pubkey,
        )
        backup_order = other_pubkey.sequence_order
        to_public_record(
            egsync_api, guardian_id, 'guardian_backup', backup,
            guardian_id=guardian_id, backup_order=backup_order
        )


def round3(guardian_id, sequence_order, egsync_api, private_dir):
    '''Round 3: verify backups
    '''

    # restore own private state
    election_key_pair = from_private_record(private_dir, 'election_key_pair')
    own_public_key = election_key_pair.share()

    # find backup files sent to self, with basenames as keys
    designated_backups = load_designated_backups(egsync_api, guardian_id)

    # load other guardians' public keys from shared folder
    other_guardian_pubkeys = {
        k.owner_id: k for k in load_guardian_pubkeys(egsync_api)
        if k.owner_id != guardian_id # remove self
    }

    for (owner_id, backup) in designated_backups.items():
        owner_public_key = other_guardian_pubkeys[owner_id]
        verification: ElectionPartialKeyVerification = \
            verify_election_partial_key_backup(
                guardian_id, # mine
                backup,
                owner_public_key, # theirs
                election_key_pair # mine
            )
        assert verification.verified == True
        # these are named identically to the corresponding guardian_backups for now
        guardian_number = int(guardian_id.split('_')[-1])
        to_public_record(
            egsync_api, guardian_id, 'guardian_verification', verification,
            guardian_id=owner_id, backup_order=guardian_number
        )


@click.command("key-ceremony")
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
    "--ceremony-round",
    prompt="Current key ceremony round",
    help="Current key ceremony round",
    type=click.INT,
)
def GuardianKeyCeremonyCommand(
    egsync_api: str,
    private_dir: str,
    guardian_id: str,
    guardian_sequence_order: int,
    ceremony_round: int,
) -> None:
    """
    This command runs one round of the key ceremony from the perspective of a
    particular .
    """

    # print(json.dumps(locals()))

    if ceremony_round == 1:
        round1(guardian_id, guardian_sequence_order, egsync_api, private_dir)

    elif ceremony_round == 2:
        round2(guardian_id, guardian_sequence_order, egsync_api, private_dir)

    elif ceremony_round == 3:
        round3(guardian_id, guardian_sequence_order, egsync_api, private_dir)

    # TODO implement round 4 (challenge if necessary)
    else:
        raise Exception(f'Invalid ceremony_round "{ceremony_round}"')


@click.command("decrypt-shares")
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
    "--guardian-id",
    prompt="Unique ID for this guardian",
    help="Unique ID for this guardian",
    type=click.STRING,
)
def DecryptSharesCommand(
    egsync_api: str,
    private_dir: str,
    guardian_id: str,
) -> None:
    """
    Compute guardian decryption shares for the tally + each spoiled ballot.
    """

    # print(json.dumps(locals()))

    # restore own private state
    election_key_pair = from_private_record(private_dir, 'election_key_pair')

    # load public info
    details   = from_public_record(egsync_api, 'ceremony_details')
    manifest  = from_public_record(egsync_api, 'manifest')
    joint_key = from_public_record(egsync_api, 'joint_key')
    (_, _, context) = build_election(details, manifest, joint_key)

    # create guardian object
    guardian = Guardian(election_key_pair, details)

    # compute tally share
    try:
        tally = from_public_record(egsync_api, 'ciphertext_tally')
        tally_share = guardian.compute_tally_share(tally, context)
        assert tally_share is not None
        # print(f'computed {guardian_id} decryption share of election tally', flush=True)
        try:
            to_public_record(
                egsync_api, guardian_id, 'tally_share', tally_share,
                guardian_id=guardian_id
            )
        except Exception as e:
            print(e)
            print('Failed to upload tally share')
    except Exception as e:
        print(e)
        print('Failed to compute tally share')

    # compute spoiled ballot shares (we don't decrypt cast ballots)
    try:
        spoiled_ballots = load_spoiled_ballots(egsync_api)
        assert len(spoiled_ballots) > 0 # TODO count to see how many there should be?
        # TODO loop over this part too to separate errors
        spoiled_shares: Dict[BallotId, Optional[DecryptionShare]] \
            = guardian.compute_ballot_shares(spoiled_ballots, context)
        for (spoiled_id, spoiled_share) in spoiled_shares.items():
            try:
                # print(f'computed {guardian_id} decryption share of {spoiled_id}', flush=True)
                assert spoiled_share is not None
            except Exception as e:
                print(e)
                print(f'Failed to compute spoiled_share for {spoiled_id}')
            try:
                to_public_record(
                    egsync_api, guardian_id, 'spoiled_share', spoiled_share,
                    spoiled_id=spoiled_id, guardian_id=guardian_id
                )
            except Exception as e:
                print(e)
                print(f'Failed to upload spoiled_share for {spoiled_id}')
    except Exception as e:
        print(e)
        print('Failed to compute (or upload) ballot shares')

    # print(flush=True)


@click.group()
def cli() -> None:
    pass

cli.add_command(GuardianKeyCeremonyCommand)
cli.add_command(DecryptSharesCommand)

if __name__ == '__main__':
    cli()
