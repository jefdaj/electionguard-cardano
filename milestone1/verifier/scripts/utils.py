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


### path maps ###
#
#  Single source of truth for how to load and save each artifact.
#  Prevents having to write out and create the data dirs multiple times.
#  Maps are dicts of informal type -> (actual type, relative dir path, basename format str)
#
#################

PRIVATE_RECORDS = {
    'election_key_pair': (
        ElectionKeyPair,
        '.',
        'election_key_pair'
    ),
    'plaintext_ballot': (
        PlaintextBallot,
        'plaintext_ballots',
        '{obj.object_id}'
    ),
}

PUBLIC_RECORDS = {
    'manifest': (
        Manifest,
        '1_config/1_announce',
        '1_manifest'
    ),
    'ceremony_details': (
        CeremonyDetails,
        '1_config/1_announce',
        '2_ceremony'
    ),
    'guardian_pubkey': (
        ElectionPublicKey,
        '1_config/2_ceremony/1_pubkeys',
        '{guardian_id}'
    ),
    'guardian_backup': (
        ElectionPartialKeyBackup,
        '1_config/2_ceremony/2_backups',
        '{guardian_id}_backup_{backup_order}'
    ),
    'guardian_verification': (
        ElectionPartialKeyVerification,
        '1_config/2_ceremony/3_verifications',
        '{guardian_id}_backup_{backup_order}'
    ),
    'joint_key': (
        ElectionJointKey,
        '1_config/3_election',
        'joint_key'
    ),
    'constants': (
        ElectionConstants,
        '1_config/3_election',
        'constants'
    ),
    'context': (
        CiphertextElectionContext,
        '1_config/3_election',
        'context'
    ),
    'device': (
        EncryptionDevice,
        '1_config/4_devices',
        'device_{device_number}'
    ),
    'ballot_submitted': (
        CiphertextBallot,
        '2_ballots/1_submitted',
        '{ballot_id}'
    ),
    'cast_notice': (
        dict,
        '2_ballots/2_cast',
        '{obj.ballot_id}'
    ),
    'ballot_spoiled': (
        CiphertextBallot,
        '2_ballots/3_spoiled',
        '{obj.object_id}'
    ),
    'ciphertext_tally': (
        PublishedCiphertextTally,
        '3_results',
        '1_tally'
    ),
    'tally_share': (
        DecryptionShare,
        '3_results/2_decrypt/1_shares/1_tally',
        'tally_{guardian_id}'
    ),
    'spoiled_share': (
        DecryptionShare,
        '3_results/2_decrypt/1_shares/2_spoiled',
        '{spoiled_id}_{guardian_id}'
    ),
    'plaintext_tally': (
        PlaintextTally,
        '3_results/2_decrypt/2_combined',
        '1_tally'
    ),
    'spoiled_result': (
        PlaintextTally,
        '3_results/2_decrypt/2_combined/2_spoiled',
        '{ballot_id}'
    ),
    'summary': (
        dict,
        '.',
        '3_results/3_summary'
    ),
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


### load and save single files ###

def to_public_record(public_dir: str, record_type: str, obj, **fmtargs):
    return to_record(PUBLIC_RECORDS, public_dir, record_type, obj, **fmtargs)

def to_private_record(private_dir: str, record_type: str, obj, **fmtargs):
    return to_record(PRIVATE_RECORDS, private_dir, record_type, obj, **fmtargs)

def from_public_record(public_dir: str, record_type: str, **fmtargs):
    return from_record(PUBLIC_RECORDS, public_dir, record_type, **fmtargs)

def from_private_record(private_dir: str, record_type: str, **fmtargs):
    return from_record(PRIVATE_RECORDS, private_dir, record_type, **fmtargs)


### load sets of files ###

# you probably want the cast or spoiled versions below
def load_ballots(
        public_dir: str,
        id_list_dir: str,
        state: Optional[BallotBoxState]
        ) -> List[SubmittedBallot]:
    ballot_ids = [splitext(n)[0] for n in listdir(id_list_dir)]
    ballots = [
        from_public_record(public_dir, 'ballot_submitted', ballot_id=bid)
        for bid in ballot_ids
    ]
    # TODO is this right? seems too simple and hacky
    if state is not None:
        for b in ballots:
            b.state = state
    return ballots

# mainly for checking that the cast + spoiled ones add up to the total
def load_submitted_ballots(public_dir: str) -> List[SubmittedBallot]:
    submitted_dir = join(public_dir, PUBLIC_RECORDS['ballot_submitted'][1])
    return load_ballots(public_dir, submitted_dir, None)

def load_cast_ballots(public_dir: str) -> List[SubmittedBallot]:
    cast_dir = join(public_dir, PUBLIC_RECORDS['cast_notice'][1])
    return load_ballots(public_dir, cast_dir, BallotBoxState.CAST)

def load_spoiled_ballots(public_dir: str) -> List[SubmittedBallot]:
    spoiled_dir = join(public_dir, PUBLIC_RECORDS['ballot_spoiled'][1])
    return load_ballots(public_dir, spoiled_dir, BallotBoxState.SPOILED)

def load_spoiled_results(public_dir: str) -> List[PlaintextTally]:
    spoiled_dir = join(public_dir, PUBLIC_RECORDS['spoiled_result'][1])
    spoiled_ids = [splitext(n)[0] for n in listdir(spoiled_dir)]
    spoiled_results = [
        from_public_record(public_dir, 'spoiled_result', ballot_id=i)
        for i in spoiled_ids
    ]
    return spoiled_results

def load_guardian_pubkeys(public_dir: str) -> List[ElectionPublicKey]:
    # for now, we just assume they're named sequentially
    # TODO come up with a cleaner way
    guardian_pubkeys: List[ElectionPublicKey] = []
    guardian_number = 0
    while True:
        guardian_number += 1
        try:
            pubkey = from_public_record(
                public_dir, 'guardian_pubkey',
                guardian_id=f'guardian_{guardian_number}'
            )
            guardian_pubkeys.append(pubkey)
        except FileNotFoundError:
            break
    assert len(guardian_pubkeys) > 0
    return guardian_pubkeys

def load_designated_backups(
        public_dir: str,
        guardian_id: GuardianId) -> Dict[str, ElectionPartialKeyBackup]:
    # same as above: assume they're named sequentially
    designated_backups: Dict[str, ElectionPartialKeyBackup] = {}
    guardian_number = int(guardian_id.split('_')[-1])
    backup_order = 0
    while True:
        backup_order += 1
        if backup_order == guardian_number:
            continue # skip self
        try:
            backup = from_public_record(
                public_dir, 'guardian_backup',
                guardian_id=f'guardian_{backup_order}',
                backup_order=guardian_number
            )
            designated_backups[backup.owner_id] = backup
        except FileNotFoundError:
            break
    assert len(designated_backups) > 0
    return designated_backups

# you probably want the tally or spoiled ballot specific versions below
def load_decryption_shares(
        share_type: str,
        public_dir: str,
        guardian_count: int,
        **fmtargs
    ) -> Dict[GuardianId, DecryptionShare]:
    shares = {}
    # we assume they're sequential, but not necessarily all present
    # TODO should the earlier fns work that way too?
    for n in range(1, guardian_count + 1):
        guardian_id = f'guardian_{n}'
        try:
            share = from_public_record(
                public_dir, share_type,
                guardian_id=guardian_id,
                **fmtargs
            )
            shares[guardian_id] = share
        except FileNotFoundError:
            print(f'WARNING {guardian_id} tally share missing')
    assert len(shares) > 0
    return shares

def load_tally_shares(public_dir, guardian_count):
    return load_decryption_shares(
        'tally_share', public_dir, guardian_count
    )

def load_spoiled_shares(public_dir, guardian_count, spoiled_id):
    return load_decryption_shares(
        'spoiled_share', public_dir, guardian_count,
        spoiled_id=spoiled_id
    )


### build electionguard objects ###

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
