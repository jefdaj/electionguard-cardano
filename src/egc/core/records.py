# from .plutus import *
from .plutus import ipfs_cid_to_string
from .plutus.types import record as r

import electionguard as eg

import random
import re
from typing import Any
from pathlib import Path
import shutil
import tempfile
import os

from .utils import make_log_call
import logging
LOG = logging.getLogger(__name__)
LOG_CALL = make_log_call(LOG.debug)


# plutus metadata type : (decode to type, dir relname, basename fmtargs ptn)
# "decode to type" is usually an eg type, but there are a few exceptions
PUBLIC_RECORD_TYPES = {
    r.Manifest: (
        eg.Manifest,
        '1_config/1_announce',
        '1_manifest'
    ),
    r.CeremonyDetails: (
        eg.CeremonyDetails,
        '1_config/1_announce',
        '2_ceremony'
    ),
    r.GuardianPubkey: (
        eg.ElectionPublicKey,
        '1_config/2_ceremony/1_pubkeys',
        'guardian_{guardian_number}'
    ),
    r.GuardianBackup: (
        eg.ElectionPartialKeyBackup,
        '1_config/2_ceremony/2_backups',
        'guardian_{guardian_number}_backup_{backup_order}'
    ),
    r.GuardianVerification: (
        eg.ElectionPartialKeyVerification,
        '1_config/2_ceremony/3_verifications',
        'guardian_{guardian_number}_backup_{backup_order}'
    ),
    r.JointKey: (
        eg.ElectionJointKey,
        '1_config/3_election',
        'joint_key'
    ),
    r.Constants: (
        eg.ElectionConstants,
        '1_config/3_election',
        'constants'
    ),
    r.Context: (
        eg.CiphertextElectionContext,
        '1_config/3_election',
        'context'
    ),
    r.Device: (
        eg.EncryptionDevice,
        '1_config/4_devices',
        'device_{device_number}'
    ),
    r.BallotSubmitted: (
        eg.CiphertextBallot, # TODO SubmittedBallot with state set to UNKNOWN?
        '2_ballots/1_submitted',
        '{ballot_id}'
    ),
    r.CastNotice: (
        r.CastNotice,
        '2_ballots/2_cast',
        '{ballot_id}'
    ),
    r.BallotSpoiled: (
        # This seems correct to me even though it doesn't match the
        # electionguard-python implementation: we *do* want to publish all
        # the nonces at this step, right? So people can decrypt immediately
        # rather than waiting for the guardians.
        eg.CiphertextBallot,
        '2_ballots/3_spoiled',
        '{ballot_id}'
    ),
    r.CiphertextTally: (
        eg.PublishedCiphertextTally, # TODO CiphertextTally? (the non-"published" version)
        '3_results',
        '1_tally'
    ),
    r.TallyShare: (
        eg.DecryptionShare,
        '3_results/2_decrypt/1_shares/1_tally',
        'tally_guardian_{guardian_number}'
    ),
    r.SpoiledShare: (
        eg.DecryptionShare,
        '3_results/2_decrypt/1_shares/2_spoiled',
        '{spoiled_id}_guardian_{guardian_number}'
    ),
    # TODO rename tally_result?
    r.PlaintextTally: (
        eg.PlaintextTally,
        '3_results/2_decrypt/2_combined',
        '1_tally'
    ),
    r.SpoiledResult: (
        eg.PlaintextTally,
        '3_results/2_decrypt/2_combined/2_spoiled',
        '{ballot_id}'
    ),
    r.Summary: (
        dict,
        '4_verify',
        '{verifier_id}'
    ),
}


def record_path(metadata: r.PublicRecordMetadata, pub_dir: Path) -> Path:
    "Find the path of a record in the public records dir by metadata."
    LOG.debug(f'metadata: {metadata}')
    if isinstance(metadata, r.PublicRecord):
        LOG.warning(f'Passed PublicRecord rather than PublicRecordMetadata: {metadata}')
        metadata = metadata.metadata
    if not isinstance(pub_dir, Path):
        pub_dir = Path(pub_dir)
    m_type = type(metadata)
    LOG.debug(f'm_type: {m_type}')
    (_egtype, dname, fstr) = PUBLIC_RECORD_TYPES[m_type]
    LOG.debug(f'dname: {dname}')
    LOG.debug(f'fstr: {fstr}')
    var_strs = {}
    for (k,v) in vars(metadata).items():
        if isinstance(v, bytes):
            v = v.decode('utf-8')
        var_strs[k] = v
    LOG.debug(f'var_strs: {var_strs}')
    fname = fstr.format(**var_strs)
    LOG.debug(f'fname: {fname}')
    path = (pub_dir / dname / fname).with_suffix('.json')
    LOG.debug(f'path: {path}')
    return path


# TODO better type for obj?
# TODO should just need metadata, not a whole record, right?
def save_record(metadata: r.PublicRecordMetadata, obj: Any, pub_dir: Path) -> Path:
    "Save a PublicRecord in the public records dir and return its path."
    fpath = record_path(metadata, pub_dir=pub_dir)
    fpath.parent.mkdir(parents=True, exist_ok=True)

    # TODO use my fancy_dumps or similar here?
    # with open(fpath, 'w') as f:
        # json.dump(obj, f)
    fpath.write_text( eg.serialize.to_raw(obj) )

    LOG.info(f'Saved {metadata} -> {fpath}')
    return fpath


_FSTR_FIELD = re.compile(r'\{(\w+)\}')

# Optional: tighten groups only for intra-fstring disambiguation
# (multiple adjacent fields in one fstring). Not needed for uniqueness
# across types.
_FIELD_PATTERNS = {
    'ballot_id':       r'ballot-[0-9a-fA-F-]{36}',
    'spoiled_id':      r'ballot-[0-9a-fA-F-]{36}',
    'guardian_number': r'\d+',
    'backup_order': r'\d+',
    'device_number': r'\d+',
}


def _fstr_to_regex(fstr: str) -> re.Pattern:
    """Turn 'guardian_{guardian_number}' into a regex with named groups."""
    parts, last = [], 0
    for m in _FSTR_FIELD.finditer(fstr):
        parts.append(re.escape(fstr[last:m.start()]))
        field = m.group(1)
        parts.append(f'(?P<{field}>{_FIELD_PATTERNS.get(field, ".+?")})')
        last = m.end()
    parts.append(re.escape(fstr[last:]))
    return re.compile('^' + ''.join(parts) + '$')


def _key(dname: str, fstr: str) -> str:
    """Unique lookup key: folder + literal filename prefix up to '{'."""
    s = f'{dname}/{fstr.split("{", 1)[0]}'
    LOG.debug(f'_key: {s}')
    return s


# Build once. Map unique (folder + literal prefix) -> (type, regex).
# Sort by key length descending so longer, more-specific prefixes win
# when one prefix is a substring-prefix of another sharing the folder.
# TODO simplify since current layout has no duplicates
_REVERSE = sorted(
    (
        (_key(dname, fstr), m_type, _fstr_to_regex(fstr))
        for m_type, (_dtype, dname, fstr) in PUBLIC_RECORD_TYPES.items()
    ),
    key=lambda t: len(t[0]),
    reverse=True,
)
LOG.debug(f'_REVERSE: {_REVERSE}')


def path_metadata(abs_path: Path, pub_dir: Path) -> r.PublicRecordMetadata:
    "Inverse of record_path: decode a json file path back to metadata."
    LOG.debug(f'abs_path: {abs_path}')
    LOG.debug(f'pub_dir: {pub_dir}')
    rel = Path(abs_path).relative_to(Path(pub_dir)).with_suffix('')
    LOG.debug(f'rel: {rel}')
    rel_str = rel.as_posix()
    LOG.debug(f'rel_str: {rel_str}')
    fname = rel.name  # filename only, folder stripped
    LOG.debug(f'fname: {fname}')

    for key, m_type, rx in _REVERSE:
        if not rel_str.startswith(key):
            continue
        m = rx.match(fname)
        if bool(m):
            LOG.debug(f'{fname} matches {rx} for type {m_type}')
        else:
            LOG.debug(f'{fname} does not match {rx} for type {m_type}')
        if not m:
            raise ValueError(
                f'Path matches {key!r} but not filename pattern: {abs_path}'
            )
        LOG.debug(f'm.groupdict: {m.groupdict()}')
        return m_type(**m.groupdict())  # mixin coerces/validates
    raise ValueError(f'No record type matches path: {abs_path}')


# TODO load_record_data?
def load_record(metadata: r.PublicRecordMetadata, pub_dir: Path):
    "Given PublicRecordMetadata, load the corresponding record object."
    mtype = type(metadata)
    LOG.debug(f'mtype: {mtype}')
    (decode_cls, _, _) = PUBLIC_RECORD_TYPES[mtype]
    LOG.debug(f'decode_cls: {decode_cls}')
    path = record_path(metadata, pub_dir)
    LOG.debug(f'path: {path}')
    if not path.exists():
        raise Exception(f'No such record: {metadata} ({path})')

    # TODO factor out a util fn for this
    # TODO unify with the static record round-trip tests?
    txt = path.read_text()
    try:
        data = eg.serialize.from_raw(decode_cls, txt)
        LOG.debug('decoded with electionguard.serialize')
    except:
        if hasattr(decode_cls, "from_json"):
            data = decode_cls.from_json(txt)
            LOG.debug(f'decoded with {decode_cls}.from_json')
        else:
            data = json.reads(txt)
            LOG.debug('decoded with json.reads')

    LOG.debug(f'data: {data}')
    assert type(data) == decode_cls
    return data


# TODO later, replace this with/turn into a verification
def load_all_guardian_pubkeys(n_guardians: int, pub_dir: Path):
    "Load all guardian pubkeys, or raise an error if any are missing."
    LOG.debug('load_all_guardian_pubkeys')
    LOG.debug(f'n_guardians: {n_guardians}')
    pub_dir = Path(pub_dir)
    LOG.debug(f'pub_dir: {pub_dir}')
    records = []
    for i in range(1, n_guardians+1):
        rec = load_record(r.GuardianPubkey(guardian_number=i), pub_dir)
        LOG.debug(f'loaded rec: {rec}')
        records.append(rec)
    return records


# TODO later, replace this with/turn into a verification
def key_ceremony_round1_complete(pub_dir: Path):
    try:
        details = load_record(r.CeremonyDetails(), pub_dir)
        LOG.debug(f'details: {details}')
        n = details.number_of_guardians
        LOG.debug(f'n guardians: {n}')
        # TODO prevent guardians from gaming this by posting an extra key
        pubkeys = load_all_guardian_pubkeys(n, pub_dir)
        LOG.debug(f'actual n_pubkeys: {len(pubkeys)}')
        return len(pubkeys) == n
    except Exception as e:
        LOG.error(e)
        return False
 

def key_ceremony_round2_complete(pub_dir: Path):
    try:
        details = load_record(r.CeremonyDetails(), pub_dir)
        LOG.debug(f'details: {details}')
        n = details.number_of_guardians
        LOG.debug(f'n guardians: {n}')
        # TODO prevent guardians from gaming this by posting extra backups
        n_backups_expected = n**2 - n
        LOG.debug(f'n_backups_expected: {n_backups_expected}')
        backups = load_all_guardian_backups(n, pub_dir)
        LOG.debug(f'actual n_backups: {len(backups)}')
        return len(backups) == n_backups_expected
    except Exception as e:
        LOG.error(e)
        return False
 

# TODO where should this live?
def load_all_guardian_backups(n_guardians: int, pub_dir: Path):
    "Load all guardian backups, or raise an error if any are missing."
    LOG.debug('load_all_guardian_backups')
    LOG.debug(f'n_guardians: {n_guardians}')
    pub_dir = Path(pub_dir)
    LOG.debug(f'pub_dir: {pub_dir}')
    records = []
    for guardian_number in range(1, n_guardians+1):
        for backup_order in range(1, n_guardians+1):
            if guardian_number == backup_order:
                LOG.debug(f'skip guardian_number {guardian_number} backup {backup_order}')
                continue # guardians don't send themselves a backup
            rec = load_record(
                r.GuardianBackup(
                    guardian_number = guardian_number,
                    backup_order    = backup_order
                ),
                pub_dir
            )
            LOG.debug(f'loaded rec: {rec}')
            records.append(rec)
    return records


def record_key(record) -> str:
    "Work around record `unhashable type` issues."
    # TODO add a method to the dataclass instead?
    # TODO use entire record including cid for key? seems more secure, but not always known?
    return str(record.metadata)


class RecordStore:
    """Manages fetching and verifying records. All save and load operations
    should go through this rather than reading or writing files directly.
    Various other objects should keep references to it for record related queries."""

    def __init__(
            self,
            records_verified_dir: Path,
            records_rejected_dir: Path,
        ):
        LOG_CALL()

        # ensure record dirs exist and are empty
        shutil.rmtree(records_verified_dir, ignore_errors=True)
        shutil.rmtree(records_rejected_dir, ignore_errors=True)
        records_verified_dir.mkdir(parents=True, exist_ok=False)
        records_rejected_dir.mkdir(parents=True, exist_ok=False)
        self.records_verified_dir: Path = records_verified_dir
        self.records_rejected_dir: Path = records_rejected_dir

        self._all_records: dict[str, r.PublicRecord] = {} # all records so far in any state
        self._pending_records: dict = {} # metadata str -> (record, attempts, next attempt)
        self._fetched_cids: set[str] = set() # set(cid)

    def key_for_record(self, record: r.PublicRecord):
        LOG_CALL()
        return record_key(record) # TODO better keys here

    def record_for_key(self, key: str):
        LOG_CALL()
        return self._all_records[key]

    def keys_for_cid(self, cid):
        "Return a list of keys for records seen so far with a given CID."
        LOG_CALL()
        return sorted([
            k for (k, r) in self._all_records.items()
            if r.ipfs_cid == cid
        ])

    def add_record_seen_on_chain(self, record):
        "Main entry point for new records seen on chain. Called by Subscriber."
        LOG_CALL()
        key = self.key_for_record(record)
        LOG.debug(f'key: {key}')
        if key in self._all_records.keys():
            LOG.info(f'add {key} ignoring duplicate')
            # TODO what should the protocol actually require in this situation?
        else:
            LOG.info(f'add {record}')
            self._all_records[key] = record
            self._pending_records[key] = (record, 0, 0)

    def fetch_successful(self, cid, data: bytes):
        """Called by IPFSService after a successful fetch. Implies the data
        matches the CID and is ready to be parsed + verified + written to disk."""
        # key = self.key_for_record(cid)
        LOG_CALL()
        cid_str = ipfs_cid_to_string(cid)
        self._fetched_cids.add(cid)
        # there may be more than one record per cid, so make a list first
        records_fetched = [
            (k, r) for (k, (r, _, _))
            in self._pending_records.items()
            if ipfs_cid_to_string(r.ipfs_cid) == cid_str
        ]

        # TODO verification here
        records_verified = records_verified

        self._save_verified_records(data, records_verified)
        # TODO also save records that fail verfification, but flag them

    def mark_attempt(self, cid, attempts, next_attempt):
        LOG_CALL()
        LOG.debug(f'all records: {self._all_records}')
        keys = self.keys_for_cid(cid)
        LOG.debug(f'keys for cid {cid}: {keys}')
        for key in keys:
            LOG.info(f'mark_attempt key:{key} attempts:{attempts} next_attempt:{next_attempt}')
            (record, _, _) = self._pending_records[key]
            self._pending_records[key] = (record, attempts, next_attempt)

    def due(self, now):
        LOG_CALL()
        # TODO should this live here or in IPFSService?
        cids_due = [
            (record.ipfs_cid, attempts)
            for (record, attempts, next_attempt) in self._pending_records.values()
            if next_attempt <= now
        ]
        if cids_due:
            LOG.debug(f'cids_due: {len(cids_due)}')
        random.shuffle(cids_due) # TODO is this a good strategy? or should they be sorted?
        return cids_due

    def n_pending_cids(self, records=[]):
        "The number of CIDs seen on chain but not yet fetched."
        # TODO remove records arg?
        LOG_CALL()
        keys = self._pending_records.keys()
        if records:
            keys = [
                k for k in keys
                if k in [self.key_for_record(r) for r in records]
            ]
        cids = set(self._all_records[k].ipfs_cid for k in keys)
        return len(cids)

    def n_unfetched_records(self, records=[]):
        """A bit like n_pending_cids, except:
        - requires a list of records
        - does not count pending CIDs for other records not passed as an arg
        - counts CIDs in those records not yet seen on chain
        - returns the number of records with unfetched CIDs, not unfetched CIDs
        """
        LOG_CALL()
        unfetched = [r for r in records if not r.ipfs_cid in self._fetched_cids]
        n           = len(records)
        n_unfetched = len(unfetched)
        n_fetched   = n - len(unfetched)
        LOG.info(f'{n_fetched}/{n} records fetched, leaving {n_unfetched} unfetched: {unfetched}')
        return n_unfetched

    def _save_verified_records(self, data, kr_pairs):
        "Multi-record version because a given CID may match more than one."
        LOG.debug(f'saving {len(kr_pairs)} verified records: {kr_pairs}')
        for (key, record) in kr_pairs:
            self._save_verified_record(data, record)
            LOG.debug(f'remove from pending_records: {key}')
            del self._pending_records[key]

    def _save_verified_record(self, data: bytes, record: r.PublicRecord):
        """Given a record and bytes matching its CID, write the bytes to the
        proper file. Returns the save path, although that isn't used so far.
        """
        LOG_CALL()
        save_path = record_path(
            record.metadata,
            pub_dir = self.records_verified_dir
        )
        LOG.debug(f'save_path: {save_path}')
        cid_str = ipfs_cid_to_string(record.ipfs_cid)
        LOG.debug(f'cid_str: {cid_str}')
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=save_path.parent, suffix=".json.part")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, save_path)
            return save_path
        finally:
            # Clean up the temp file if anything failed before the replace
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass
