# TODO make an object (DotMap?) describing all the file paths here
# TODO functions for repeated click options

# TODO remove unused imports
from electionguard import serialize
from electionguard.ballot import (PlaintextBallot,PlaintextBallotSelection,PlaintextBallotContest,SubmittedBallot,CiphertextBallot)
from electionguard.ballot_box import (BallotBoxState)
from electionguard.constants import ElectionConstants, get_constants
from electionguard.data_store import DataStore
from electionguard.decryption import (compute_decryption_share,compute_decryption_share_for_ballot)
from electionguard.decryption_share import DecryptionShare
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice, EncryptionMediator, contest_from, generate_device_uuid
from electionguard.key_ceremony import (CeremonyDetails, ElectionJointKey,ElectionKeyPair,ElectionPublicKey,ElectionPartialKeyBackup,ElectionPartialKeyVerification,combine_election_public_keys, generate_election_key_pair,generate_election_partial_key_backup,verify_election_partial_key_backup)
from electionguard.manifest import Manifest, InternalManifest, Language
from electionguard.tally import (CiphertextTally,PublishedCiphertextTally,PlaintextTally)
from electionguard.type import GuardianId
from electionguard.utils import get_optional
from electionguard_tools.helpers.election_builder import ElectionBuilder
from os import makedirs, listdir
from os.path import join, splitext
from pprint import pprint
from typing import Dict, List, Tuple, Optional
import json
import uuid


# hide INFO dumps of crypto from elgamal.py
import logging
logging.getLogger('electionguard').setLevel(logging.WARNING)


def build_election(
            details: CeremonyDetails,
            manifest: Manifest,
            joint_key: ElectionJointKey
        ) -> Tuple[
            ElectionConstants,
            InternalManifest,
            CiphertextElectionContext
        ]:

    election_builder = ElectionBuilder(
        details.number_of_guardians,
        details.quorum,
        manifest,
    )

    # TODO add this using IPFS later
    # if verification_url is not None:
    #     election_builder.add_extended_data_field(
    #         self.VERIFICATION_URL_NAME, verification_url
    #     )

    # click.echo("Creating context and internal manifest")

    # from electionguard_tools/factories/election_factory
    election_builder.set_public_key(
        get_optional(joint_key).joint_public_key
    )
    election_builder.set_commitment_hash(
        get_optional(joint_key).commitment_hash
    )

    internal_manifest: InternalManifest
    context:           CiphertextElectionContext
    constants:         ElectionConstants
    internal_manifest, context = get_optional(election_builder.build())
    constants = get_constants()

    return (constants, internal_manifest, context)

# you probably want the cast or spoiled versions below
def load_submitted_ballots(
        public_dir: str,
        id_list_dir: str,
        state: BallotBoxState
        ) -> List[SubmittedBallot]:
    ballot_ids = [splitext(n)[0] for n in listdir(id_list_dir)]
    ballots = [
        from_public_record(public_dir, 'ballot_submitted', ballot_id=bid)
        for bid in ballot_ids
    ]
    # TODO is this right? seems too simple and hacky
    for b in ballots:
        b.state = state
    return ballots

def load_cast_ballots(public_dir: str, cast_dir: str) -> List[SubmittedBallot]:
    return load_submitted_ballots(public_dir, cast_dir, BallotBoxState.CAST)

def load_spoiled_ballots(public_dir: str, spoiled_dir: str) -> List[SubmittedBallot]:
    return load_submitted_ballots(public_dir, spoiled_dir, BallotBoxState.SPOILED)


def load_device_by_number(devices_dir: str, device_number: int) -> EncryptionDevice:
    # TODO keep track of their IDs instead?
    i = device_number - 1
    device_path = join(devices_dir, sorted(listdir(devices_dir))[i])
    # print(device_path)
    device = serialize.from_file(EncryptionDevice, device_path)
    return device


# TODO name something clearer in the context of referendum questions?
def find_candidate_id(manifest: Manifest, candidate_name: str) -> Optional[str]:
    candidate_name_en = Language(language='en', value=candidate_name)
    for candidate in manifest.candidates:
        for name_variant in candidate.name.text:
            if name_variant == candidate_name_en:
                return candidate.object_id
    return None


def build_ballot(
        manifest: Manifest,
        candidate_name: str,
    ) -> PlaintextBallot:

    ballot_id = f"ballot-{uuid.uuid1()}"
    style_id  = 'ballot-style-01'

    candidate_id = find_candidate_id(manifest, candidate_name)
    selection_id = f'{candidate_id}-selection' # TODO clean this up!

    # TODO any reason to include the non-chosen selections too here?
    #      the example data sometimes does
    selections = [
        PlaintextBallotSelection(
            vote=1,
            is_placeholder_selection=False,
            object_id=selection_id
        )
    ]

    contests = [
        PlaintextBallotContest(
            object_id="referendum-pineapple",
            ballot_selections=selections
        )
    ]

    ballot = PlaintextBallot(ballot_id, style_id, contests)

    return ballot


def load_guardian_pubkeys(public_dir: str) -> List[ElectionPublicKey]:
    guardian_pubkeys: List[ElectionPublicKey] = []
    for json_filename in listdir(public_dir):
        guardian_id: GuardianId = splitext(json_filename)[0]
        json_path = join(public_dir, json_filename)
        guardian_pubkey = serialize.from_file(ElectionPublicKey, json_path)
        guardian_pubkeys.append(guardian_pubkey)
    return guardian_pubkeys


def load_designated_backups(backups_dir: str, guardian_id: GuardianId) -> Dict[str, ElectionPartialKeyBackup]:
    # TODO use own public key to pick them out rather than filename?
    designated_backups: Dict[str, ElectionPartialKeyBackup] = {}
    for json_filename in listdir(backups_dir):
        json_path = join(backups_dir, json_filename)
        json_name = splitext(json_filename)[0]
        backup = serialize.from_file(ElectionPartialKeyBackup, json_path)
        if backup.designated_id == guardian_id:
            designated_backups[json_name] = backup
    return designated_backups

def load_guardian_decryption_shares(
        path_prefix: str,
        guardian_count: int
    ) -> Dict[GuardianId, DecryptionShare]:
    shares = {}
    for n in range(1, guardian_count + 1):
        guardian_id = f'guardian_{n}'
        share_path = f'{path_prefix}_{guardian_id}.json'
        share = serialize.from_file(DecryptionShare, share_path)
        shares[guardian_id] = share
    return shares


### paths ###
#
# prevents having to write out and create the data dirs multiple times
# dict of informal type str -> (actual type, dirname, basename format str)
#
#############

PRIVATE_RECORDS = {
    'election_key_pair': (ElectionKeyPair, '.', 'election_key_pair'),
    'plaintext_ballot': (PlaintextBallot, 'plaintext_ballots', '{obj.object_id}'),
}

PUBLIC_RECORDS = {
    'manifest': (Manifest, '1_announce', '1_manifest'),
    'ceremony_details': (CeremonyDetails, '1_announce', '2_ceremony'),
    'joint_key': (ElectionJointKey, '3_election', 'joint_key'),
    'constants': (ElectionConstants, '3_election', 'constants'),
    'context': (CiphertextElectionContext, '3_election', 'context'),
    'guardian_pubkey': (ElectionPublicKey, '2_ceremony/1_pubkeys', '{guardian_id}'),
    'guardian_backup': (ElectionPartialKeyBackup, '2_ceremony/2_backups', '{guardian_id}_backup_{backup_order}'),
    'guardian_verification': (ElectionPartialKeyVerification, '2_ceremony/3_verifications', '{json_name}'),
    'device': (EncryptionDevice, '4_devices', 'device_{obj.device_id}'),
    'ciphertext_tally': (PublishedCiphertextTally, '.', '6_tally'),
    'plaintext_tally': (PlaintextTally, '7_decrypt/2_final', '1_tally'),
    'tally_share': (DecryptionShare, '7_decrypt/1_shares/1_tally', 'tally_{guardian_id}'),
    'spoiled_share': (DecryptionShare, '7_decrypt/1_shares/2_spoiled', '{spoiled_id}_{guardian_id}'),
    'spoiled_result': (PlaintextTally, '7_decrypt/2_final/2_spoiled', '{ballot_id}'),
    'ballot_submitted': (CiphertextBallot, '5_ballots/1_submitted', '{ballot_id}'),
    'cast_notice': (dict, '5_ballots/2_cast', '{obj.ballot_id}'),
    'ballot_spoiled': (CiphertextBallot, '5_ballots/3_spoiled', '{obj.object_id}'),
    'summary': (dict, '.', '8_summary'),
}

# you probably want the public or private versions below
def to_record(records_map, public_dir: str, record_type: str, obj, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(public_dir, dname)
    makedirs(dpath, exist_ok=True)
    fmtargs['obj'] = obj # so we can use its fields too
    fname = fstr.format(**fmtargs)
    serialize.to_file(obj, fname, dpath)

# you probably want the public or private versions below
def from_record(records_map, public_dir: str, record_type: str, **fmtargs):
    (rtype, dname, fstr) = records_map[record_type]
    dpath = join(public_dir, dname)
    fname = fstr.format(**fmtargs) + '.json'
    fpath = join(dpath, fname)
    return serialize.from_file(rtype, fpath)

def to_public_record(public_dir: str, record_type: str, obj, **fmtargs):
    return to_record(PUBLIC_RECORDS, public_dir, record_type, obj, **fmtargs)

def to_private_record(private_dir: str, record_type: str, obj, **fmtargs):
    return to_record(PRIVATE_RECORDS, private_dir, record_type, obj, **fmtargs)

def from_public_record(public_dir: str, record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, public_dir, record_type, **fmtargs)

def from_private_record(private_dir: str, record_type: str, **fmtargs):
    return from_record(PRIVATE_RECORDS, private_dir, record_type, **fmtargs)
