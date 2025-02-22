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
)


import click
import json

from os import listdir, makedirs
from os.path import join, splitext
from pprint import pprint
from typing import List, Dict

from electionguard.guardian import Guardian
from electionguard import serialize
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


ELECTION_KEY_PAIR_NAME = 'election_key_pair'
MANIFEST_NAME  = '1_manifest'
JOINT_KEY_NAME = 'jointkey'


def round1(guardian_id, sequence_order, quorum, public_records_dir, private_records_dir):
    '''Round 1: create and share pubkeys
    '''

    # set up dirs
    pubkeys_dir   = join(public_records_dir, '2_ceremony/1_pubkeys')
    makedirs(pubkeys_dir  , exist_ok=True)

    # generate election key pair
    # NOTE there will eventually also be separate a Cardano wallet key pair
    election_key_pair: ElectionKeyPair = generate_election_key_pair(guardian_id, sequence_order, quorum)
    serialize.to_file(election_key_pair, ELECTION_KEY_PAIR_NAME, private_records_dir)

    # share the public key (and other info)
    # TODO why not publish_record here? I guess that's later after backups?
    public_key: ElectionPublicKey = election_key_pair.share()
    serialize.to_file(public_key, guardian_id, pubkeys_dir)



def round2(guardian_id, sequence_order, public_records_dir, private_records_dir):
    '''Round 2: create and share backups
    '''

    # set up dirs
    pubkeys_dir = join(public_records_dir, '2_ceremony/1_pubkeys')
    backups_dir = join(public_records_dir, '2_ceremony/2_backups')
    makedirs(pubkeys_dir, exist_ok=True)
    makedirs(backups_dir, exist_ok=True)

    # restore own private state
    election_key_pair_path = join(private_records_dir, ELECTION_KEY_PAIR_NAME + '.json')
    election_key_pair = serialize.from_file(ElectionKeyPair, election_key_pair_path)

    # load other guardians' public keys from shared folder
    other_guardian_pubkeys = [
        k for k in load_guardian_pubkeys(pubkeys_dir)
        if k.owner_id != guardian_id # remove self
    ]

    # save partial backups in shared folder, encrypted to each other guardians' pubkeys
    # NOTE these will be public and on-chain in my version, unless that's bad?
    for other_pubkey in other_guardian_pubkeys:
        backup = generate_election_partial_key_backup(
            guardian_id,
            election_key_pair.polynomial,
            other_pubkey,
        )
        backup_order = other_pubkey.sequence_order
        backup_name = f'{guardian_id}_backup_{backup_order}'
        serialize.to_file(backup, backup_name, backups_dir)



def round3(guardian_id, sequence_order, public_records_dir, private_records_dir):
    '''Round 3: verify backups
    '''

    # set up dirs
    pubkeys_dir       = join(public_records_dir, '2_ceremony/1_pubkeys')
    backups_dir       = join(public_records_dir, '2_ceremony/2_backups')
    verifications_dir = join(public_records_dir, '2_ceremony/3_verifications')
    makedirs(pubkeys_dir, exist_ok=True)
    makedirs(backups_dir, exist_ok=True)
    makedirs(verifications_dir, exist_ok=True)

    # restore own private state
    election_key_pair_path = join(private_records_dir, ELECTION_KEY_PAIR_NAME + '.json')
    election_key_pair = serialize.from_file(ElectionKeyPair, election_key_pair_path)
    own_public_key = election_key_pair.share()

    # find backup files sent to self, with basenames as keys
    designated_backups = load_designated_backups(backups_dir, guardian_id)

    # load other guardians' public keys from shared folder
    other_guardian_pubkeys = {
        k.owner_id: k for k in load_guardian_pubkeys(pubkeys_dir)
        if k.owner_id != guardian_id # remove self
    }

    for (json_name, backup) in designated_backups.items():
        owner_id = backup.owner_id
        owner_public_key = other_guardian_pubkeys[owner_id]
        verification: ElectionPartialKeyVerification = verify_election_partial_key_backup(
            guardian_id, # mine
            backup,
            owner_public_key, # theirs
            election_key_pair # mine
        )
        assert verification.verified == True
        # these are named identically to the corresponding guardian_backups for now
        serialize.to_file(verification, json_name, verifications_dir)

@click.command("key-ceremony")
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
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
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
    # print(json.dumps(locals()))
    if current_round == 1:
        round1(guardian_id, guardian_sequence_order, quorum, public_records_dir, private_records_dir)
    elif current_round == 2:
        round2(guardian_id, guardian_sequence_order, public_records_dir, private_records_dir)
    elif current_round == 3:
        round3(guardian_id, guardian_sequence_order, public_records_dir, private_records_dir)
    # TODO implement round 4 (challenge if necessary)
    else:
        raise Exception(f'Invalid current_round "{current_round}"')

@click.command("decrypt-shares")
@click.option(
    "--public-records-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
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
    prompt="Unique ID for this guardian",
    help="Unique ID for this guardian",
    type=click.STRING,
)
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
def DecryptSharesCommand(
    public_records_dir: str,
    private_records_dir: str,
    guardian_id: str,
    guardian_count: int,
    quorum: int,
) -> None:
    """
    Compute guardian decryption shares for the tally + all spoiled ballots.
    """
    # print(json.dumps(locals()))

    # set up dirs
    announce_dir  = join(public_records_dir, '1_announce')
    setup_dir     = join(public_records_dir, '3_election')
    ballots_dir   = join(public_records_dir, '5_ballots')
    submitted_dir = join(ballots_dir       , '1_submitted')
    cast_dir      = join(ballots_dir       , '2_cast')
    spoiled_dir   = join(ballots_dir       , '3_spoiled')

    # restore own private state
    # TODO make a function
    election_key_pair_path = join(private_records_dir, ELECTION_KEY_PAIR_NAME + '.json')
    election_key_pair = serialize.from_file(ElectionKeyPair, election_key_pair_path)
    # print('election_key_pair:'); pprint(election_key_pair)

    # load required info
    # TODO make a function if it turns out to be the proper way
    manifest_path = join(announce_dir, MANIFEST_NAME + '.json')
    manifest = serialize.from_file(Manifest, manifest_path)
    joint_key_path = join(setup_dir, JOINT_KEY_NAME + '.json')
    joint_key = serialize.from_file(ElectionJointKey, joint_key_path)
    (constants, internal_manifest, context) = build_election(
        guardian_count,
        quorum,
        manifest,
        joint_key
    )

    # restore tally
    # aha, you can deserialize these! you just need the Published version
    tally_path = join(public_records_dir, '6_tally.json')
    tally = serialize.from_file(PublishedCiphertextTally, tally_path)

    # create guardian object
    details = CeremonyDetails(guardian_count, quorum) # TODO load from file
    guardian = Guardian(election_key_pair, details)

    # compute_tally_share
    tally_share = guardian.compute_tally_share(tally, context)
    print(f'decrypted {guardian_id} share of election tally')
    assert tally_share is not None
    # print('tally share:'); pprint(tally_share)

    # TODO compute_ballot_shares
    # TODO have to check whether any are None?
    spoiled_ballots = load_spoiled_ballots(submitted_dir, spoiled_dir)
    ballot_shares = guardian.compute_ballot_shares(spoiled_ballots, context)
    for (ballot_id, ballot_share) in ballot_shares.items():
        print(f'decrypted {guardian_id} share of {ballot_id}')
        assert ballot_share is not None

    raise SystemExit


@click.group()
def cli() -> None:
    pass

cli.add_command(GuardianKeyCeremonyCommand)
cli.add_command(DecryptSharesCommand)

if __name__ == '__main__':
    cli()
