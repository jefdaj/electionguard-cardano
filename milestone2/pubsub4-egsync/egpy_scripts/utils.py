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
from electionguard.type import GuardianId, BallotId
from electionguard.utils import get_optional
from electionguard_tools.helpers.election_builder import ElectionBuilder
from os import makedirs, listdir
from os.path import join, splitext
from pprint import pprint
from typing import Dict, List, Tuple, Optional
import json
import uuid
from io import StringIO
from dataclasses import dataclass, field
import requests
from urllib.parse import urlencode
from pydantic.json import pydantic_encoder

# hide INFO dumps of crypto from elgamal.py
import logging
logging.getLogger('electionguard').setLevel(logging.WARNING)

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

@dataclass
class CastNotice:
    ballot_id: BallotId

    # timestamp, which should be in a window after ballot submitted
    cast_at: str # TODO int using from_ticks?


# TODO dataclass Summary


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
        '{ballot_id}'
    ),
}

# TODO fix local-election scripts to use ballot_id rather than obj.whatever_id
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
        CiphertextBallot, # TODO SubmittedBallot with state set to UNKNOWN?
        '2_ballots/1_submitted',
        '{ballot_id}'
    ),
    'cast_notice': (
        CastNotice,
        '2_ballots/2_cast',
        '{ballot_id}'
    ),
    'ballot_spoiled': (

        # This seems correct to me even though it doesn't match the
        # electionguard-python implementation: we *do* want to publish all
        # the nonces at this step, right? So people can decrypt immediately
        # rather than waiting for the guardians.
        CiphertextBallot,

        '2_ballots/3_spoiled',
        '{ballot_id}'
    ),
    'ciphertext_tally': (
        PublishedCiphertextTally, # TODO CiphertextTally? (the non-"published" version)
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
    # TODO rename tally_result?
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
        '4_verify',
        '{verifier_id}'
    ),
}

### get record filenames ###

# TODO put public in the name
def record_basename(record_type:str, **fmtargs):
    'So far, only used to simplify verifier summary json keys'
    (_, _, fstr) = PUBLIC_RECORDS[record_type]
    fname = fstr.format(**fmtargs)
    return fname

# you probably want the public/private specialized versions below
def record_path(records_map, root_dir:str, record_type: str, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(root_dir, dname)
    makedirs(dpath, exist_ok=True) # TODO make the dir here?
    fname = fstr.format(**fmtargs)
    return join(dpath, fname + '.json')

def private_path(private_dir: str, record_type: str, **fmtargs):
    return record_path(PUBLIC_RECORDS, private_dir, record_type, **fmtargs)


### misc ###

def make_session_with_retry(
    total=10,
    backoff_factor=0.5,
    status_forcelist=(404, 500, 502, 503, 504),
):
    """Add retries with exponential backoff to API requests.
    Usage:
      session = make_session_with_retry()
      resp = session.get(...)
      resp.raise_for_status()
    """
    retry = Retry(
        total=total,
        read=total,
        connect=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


### mint channel ###

def mint_channel(egsync_api: str, sender_channel: str, new_channel_name: str, **fmtargs):
    url = f"{egsync_api}/channels"
    fmtargs['channel'] = sender_channel
    fmtargs['new_channel_name'] = new_channel_name
    url = f"{url}?{urlencode(fmtargs)}"
    resp = make_session_with_retry().post(url, timeout=5) # TODO is some payload required?
    resp.raise_for_status()  # raise if 4xx/5xx

### load and save single files ###

def _public_record_url(egsync_api: str, record_type: str, **fmtargs) -> str:
    url = f"{egsync_api}/public_records/{record_type}"
    url = f"{url}?{urlencode(fmtargs)}" # TODO ok if no fmtargs?
    return url

def to_jsonable(obj):
    """
    Return a JSON-serializable structure (dict/list/str/...) using the same
    rules as json.dumps(..., default=pydantic_encoder).
    """
    # First turn any custom types into JSON primitives using pydantic_encoder,
    # then parse back into Python so `requests` / Flask `jsonify` can handle it.
    return json.loads(json.dumps(obj, default=pydantic_encoder))

def to_public_record(egsync_api: str, channel: str, record_type: str, obj, **fmtargs):
    """
    Remote version of to_public_record.
    """
    # serialize Python object → JSON-serializable dict
    # raw = serialize.to_raw(obj).encode(serialize.BYTE_ENCODING)
    payload = to_jsonable(obj)
    # print(type(payload))
    # pprint(egsync_api)
    # pprint(payload)

    fmtargs['channel'] = channel
    url = _public_record_url(egsync_api, record_type, **fmtargs)
    # print(url)
    resp = make_session_with_retry().post(url, json=payload, timeout=5)
    resp.raise_for_status()  # raise if 4xx/5xx

def from_public_record(egsync_api: str, record_type: str, **fmtargs):
    """
    Remote version of from_public_record.
    """
    url = _public_record_url(egsync_api, record_type, **fmtargs)
    resp = make_session_with_retry().get(url, timeout=5)
    if resp.status_code == 404:
        return None  # or raise a custom exception
    resp.raise_for_status()

    # raw = resp.json()
    # print('resp json:'); pprint(raw)
    raw = resp.text
    # print('raw class:', type(raw))
    # print('resp text:'); pprint(resp.text)

    rtype, _, _ = PUBLIC_RECORDS[record_type]
    # obj = serialize.from_dict(rtype, raw)
    obj = serialize.from_raw(rtype, raw)
    return obj

# you probably want the public or private versions below
def to_record(records_map, records_dir: str, record_type: str, obj, **fmtargs):
    (_, dname, fstr) = records_map[record_type]
    dpath = join(records_dir, dname)
    makedirs(dpath, exist_ok=True)
    # fmtargs['obj'] = obj # so we can use its fields too
    fname = fstr.format(**fmtargs)
    serialize.to_file(obj, fname, dpath)

# you probably want the public or private versions below
def from_record(records_map, records_dir: str, record_type: str, **fmtargs):
    (rtype, dname, fstr) = records_map[record_type]
    dpath = join(records_dir, dname)
    fname = fstr.format(**fmtargs) + '.json'
    fpath = join(dpath, fname)
    return serialize.from_file(rtype, fpath)

def to_private_record(private_dir: str, record_type: str, obj, **fmtargs):
    return to_record(PRIVATE_RECORDS, private_dir, record_type, obj, **fmtargs)

# def from_public_record(egsync_api: str, record_type: str, **fmtargs):
#     return from_record(PUBLIC_RECORDS, egsync_api, record_type, **fmtargs)

def from_private_record(private_dir: str, record_type: str, **fmtargs):
    return from_record(PRIVATE_RECORDS, private_dir, record_type, **fmtargs)


### list all expected fmtargs for artifacts of a given type ###

def list_record_fmtargs(egsync_api: str, record_type: str) -> List[dict]:
    url = f"{egsync_api}/record_fmtargs/{record_type}"
    resp = make_session_with_retry().get(url, timeout=5)
    if resp.status_code == 404:
        return None  # or raise a custom exception
    resp.raise_for_status()
    return resp.json()

# TODO rewrite with api
# def list_ballot_ids(id_list_dir):
#     # TODO catch FileNotFoundError here? may not always want to swallow it
#     return [
#         splitext(n)[0]
#         for n in listdir(id_list_dir)
#         if n.startswith('ballot-') # TODO remove? may only be relevant for vim swapfiles
#     ]

# TODO rewrite with api
def list_cast_ballot_fmtargs(public_dir):
    cast_dir = join(public_dir, PUBLIC_RECORDS['cast_notice'][1])
    try:
        ids = list_ballot_ids(cast_dir)
    except FileNotFoundError:
        # probably there were no cast ballots
        ids = []
    return [{'ballot_id': i} for i in ids]

# TODO rewrite with api
def list_spoiled_ballot_fmtargs(public_dir):
    spoiled_dir = join(public_dir, PUBLIC_RECORDS['ballot_spoiled'][1])
    try:
        ids = list_ballot_ids(spoiled_dir)
    except FileNotFoundError:
        # probably there were no spoiled ballots
        ids = []
    return [{'ballot_id': i} for i in ids]

# TODO rewrite with api
def list_guardian_pubkey_fmtargs(public_dir, n_guardians):
    fmtargs_list = []
    for n in range(1, n_guardians+1):
        fmtargs_list.append({'guardian_id': f'guardian_{n}'})
    return fmtargs_list

# TODO rewrite with api
def list_guardian_backup_fmtargs(public_dir, n_guardians):
    fmtargs_list = []
    for n in range(1, n_guardians+1):
        guardian_id = f'guardian_{n}'
        for backup_order in range(1, n_guardians+1):
            if backup_order == n:
                continue
            fmtargs_list.append({
                'guardian_id': guardian_id,
                'backup_order': backup_order
            })
    return fmtargs_list

# TODO rewrite with api
def list_guardian_verification_fmtargs(public_dir, n_guardians):
    return list_guardian_backup_fmtargs(public_dir, n_guardians)


### load sets of files ###

# TODO rewrite with api
# you probably want the cast or spoiled versions below
def load_ballots(
        public_dir: str,
        id_list_dir: str,
        state: Optional[BallotBoxState]
        ) -> List[SubmittedBallot]:
    ballot_ids = list_ballot_ids(id_list_dir)
    ballots = [
        from_public_record(public_dir, 'ballot_submitted', ballot_id=bid)
        for bid in ballot_ids
    ]
    # TODO is this right? seems too simple and hacky
    if state is not None:
        for b in ballots:
            b.state = state
    return ballots

# TODO rewrite with api
# mainly for checking that the cast + spoiled ones add up to the total
def load_submitted_ballots(public_dir: str) -> List[SubmittedBallot]:
    submitted_dir = join(public_dir, PUBLIC_RECORDS['ballot_submitted'][1])
    try:
        return load_ballots(public_dir, submitted_dir, None)
    except FileNotFoundError:
        # probably no submitted ballots
        return []

# TODO rewrite with api
def load_cast_ballots(public_dir: str) -> List[SubmittedBallot]:
    cast_dir = join(public_dir, PUBLIC_RECORDS['cast_notice'][1])
    try:
        return load_ballots(public_dir, cast_dir, BallotBoxState.CAST)
    except FileNotFoundError:
        # no cast ballots
        return []

# TODO rewrite with api
# TODO load these directly from spoiled_ballots dir? or check that == submitted?
def load_spoiled_ballots(public_dir: str) -> List[SubmittedBallot]:
    spoiled_dir = join(public_dir, PUBLIC_RECORDS['ballot_spoiled'][1])
    try:
        return load_ballots(public_dir, spoiled_dir, BallotBoxState.SPOILED)
    except FileNotFoundError:
        # no spoiled ballots
        return []

# TODO rewrite with api
def load_spoiled_results(public_dir: str) -> List[PlaintextTally]:
    spoiled_dir = join(public_dir, PUBLIC_RECORDS['spoiled_result'][1])
    try:
        spoiled_ids = [
            splitext(n)[0]
            for n in listdir(spoiled_dir)
            if n.startswith('ballot-')
        ]
    except FileNotFoundError:
        spoiled_ids = []
    spoiled_results = [
        from_public_record(public_dir, 'spoiled_result', ballot_id=i)
        for i in spoiled_ids
    ]
    return spoiled_results

def load_guardian_pubkeys(egsync_api: str) -> List[ElectionPublicKey]:
    ceremony_details: CeremonyDetails = from_public_record(egsync_api, 'ceremony_details')
    guardian_pubkeys: List[ElectionPublicKey] = []
    for guardian_number in range(1, ceremony_details.number_of_guardians+1):
        pubkey = from_public_record(
            egsync_api, 'guardian_pubkey',
            guardian_id=f'guardian_{guardian_number}'
        )
        guardian_pubkeys.append(pubkey)
    assert len(guardian_pubkeys) == ceremony_details.number_of_guardians
    return guardian_pubkeys

def load_guardian_pubkeys_dict(egsync_api: str) -> Dict[GuardianId, ElectionPublicKey]:
    pubkeys_list = load_guardian_pubkeys(egsync_api)
    pubkeys_dict = {key.owner_id: key for key in pubkeys_list}
    return pubkeys_dict

def load_designated_backups(egsync_api: str, guardian_id: GuardianId) -> Dict[str, ElectionPartialKeyBackup]:
    ceremony_details: CeremonyDetails = from_public_record(egsync_api, 'ceremony_details')
    designated_backups: Dict[str, ElectionPartialKeyBackup] = {}
    guardian_number = int(guardian_id.split('_')[-1])
    for backup_order in range(1, ceremony_details.number_of_guardians+1):
        if backup_order == guardian_number:
            continue # skip self
        backup = from_public_record(
            egsync_api, 'guardian_backup',
            guardian_id=f'guardian_{backup_order}',
            backup_order=guardian_number
        )
        # print(f'backup {guardian_id} {backup_order}: {backup}')
        designated_backups[backup.owner_id] = backup
    # assert len(designated_backups) == ceremony_details.number_of_guardians - 1
    return designated_backups

# you probably want the tally or spoiled ballot specific versions below
def load_decryption_shares(
        share_type: str,
        egsync_api: str,
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
                egsync_api, share_type,
                guardian_id=guardian_id,
                **fmtargs
            )
            shares[guardian_id] = share
        except FileNotFoundError:
            msg = f'WARNING {guardian_id} {share_type} missing'
            if len(fmtargs) > 0:
                msg += f' {fmtargs}'
            print(msg)
    # assert len(shares) > 0

    # This shouldn't be required, but the ElectionGuard code actually goes into
    # an infinite loop if you try to decrypt with fewer than all the shares
    # available. OK for a demo but obviously not production.
    # TODO is there an easy workaround besides failing early?
    assert len(shares) == guardian_count

    return shares

def load_tally_shares(egsync_api, guardian_count):
    return load_decryption_shares(
        'tally_share', egsync_api, guardian_count
    )

def load_spoiled_shares(egsync_api, guardian_count, spoiled_id):
    return load_decryption_shares(
        'spoiled_share', egsync_api, guardian_count,
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

# based on:
# docs.python.org/3/howto/logging-cookbook.html#using-a-context-manager-for-selective-logging
# gist.github.com/66Ton99/b13c2867adef506554a4
class CaptureLog:

    def __init__(self, level=None, close=True):
        self.logger = logging.getLogger('electionguard')
        self.log_buffer = StringIO()
        self.handler = logging.StreamHandler(self.log_buffer)
        self.level = level
        self.close = close

    def __enter__(self):

        # remove original handlers and add the temporary one
        self.old_handlers = list(h for h in self.logger.handlers)
        self.logger.handlers.clear()
        self.logger.addHandler(self.handler)

        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)

        # for use within the context manager block
        return self.log_buffer

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.close:
            self.handler.close()

        # remove temporary handler and put back the originals
        self.logger.handlers.clear()
        for h in self.old_handlers:
            self.logger.addHandler(h)

        # implicit return of None => don't swallow exceptions

def init_log(logfile, level=logging.WARNING):
    log = logging.getLogger(__name__)
    log.setLevel(level)
    if logfile is None:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(logfile)
    # handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log
