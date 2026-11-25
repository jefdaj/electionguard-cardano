from pathlib import Path
from typing import Any

import electionguard as eg
import hashlib
import os
import random
import re
import shutil
import tempfile

from .plutus import ipfs_cid_to_string
from .plutus.types import record as r
from .utils import make_log_call

import logging
LOG = logging.getLogger(__name__)
LOG_CALL = make_log_call(LOG.debug)


# TODO different module for these load_all* fns vs store vs metadata key machinery?


# Record metadata can be encoded to or decoded from a unique relative path
# using PUBLIC_RECORD_TYPES below. The path can be used as a hashable key for
# sets and dicts.
type RecordMetadataRelPath = Path


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


def metadata_to_path(metadata: r.PublicRecordMetadata, rec_dir: Path) -> Path:
    "Find the full path of a record in a records dir by metadata."
    LOG_CALL()
    relpath = metadata_to_relpath(metadata)
    if not isinstance(rec_dir, Path):
        rec_dir = Path(rec_dir)
    path = rec_dir / relpath
    LOG.debug(f'path: {path}')
    return path


def metadata_to_relpath(metadata: r.PublicRecordMetadata) -> RecordMetadataRelPath:
    "Encode record metdata as a relative path."
    LOG_CALL()
    LOG.debug(f'metadata: {metadata}')
    if isinstance(metadata, r.PublicRecord):
        LOG.warning(f'Passed PublicRecord rather than PublicRecordMetadata: {metadata}')
        metadata = metadata.metadata
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
    relpath = (dname / fname).with_suffix('.json')
    LOG.debug(f'relpath: {relpath}')
    return relpath


# TODO better type for obj?
# TODO should just need metadata, not a whole record, right?
# def save_record(metadata: r.PublicRecordMetadata, obj: Any, pub_dir: Path) -> Path:
#     "Save a PublicRecord in the public records dir and return its path."
#     fpath = record_path(metadata, pub_dir=pub_dir)
#     fpath.parent.mkdir(parents=True, exist_ok=True)
#
#     # TODO use my fancy_dumps or similar here?
#     # with open(fpath, 'w') as f:
#         # json.dump(obj, f)
#     fpath.write_text( eg.serialize.to_raw(obj) )
#
#     LOG.info(f'Saved {metadata} -> {fpath}')
#     return fpath


_FSTR_FIELD = re.compile(r'\{(\w+)\}')


# Optional: tighten groups only for intra-fstring disambiguation
# (multiple adjacent fields in one fstring). Not needed for uniqueness
# across types.
_FIELD_PATTERNS = {
    'ballot_id':       r'ballot-[0-9a-fA-F-]{36}',
    'spoiled_id':      r'ballot-[0-9a-fA-F-]{36}',
    'guardian_number': r'\d+',
    'backup_order':    r'\d+',
    'device_number':   r'\d+',
}


def _fstr_to_regex(fstr: str) -> re.Pattern:
    "Turn for example 'guardian_{guardian_number}' into a regex with named groups."
    parts, last = [], 0
    for m in _FSTR_FIELD.finditer(fstr):
        parts.append(re.escape(fstr[last:m.start()]))
        field = m.group(1)
        parts.append(f'(?P<{field}>{_FIELD_PATTERNS.get(field, ".+?")})')
        last = m.end()
    parts.append(re.escape(fstr[last:]))
    return re.compile('^' + ''.join(parts) + '$')


def _relpath_to_metadata_key(dname: str, fstr: str) -> str:
    "Unique lookup key: folder + literal filename prefix up to '{'."
    s = f'{dname}/{fstr.split("{", 1)[0]}'
    LOG.debug(f'_relpath_to_metadata_key: {s}')
    return s


# Build once. Map unique (folder + literal prefix) -> (type, regex).
# Sort by key length descending so longer, more-specific prefixes win
# when one prefix is a substring-prefix of another sharing the folder.
# TODO simplify since current layout has no duplicates
_RELPATH_TO_METADATA = sorted(
    (
        (_relpath_to_metadata_key(dname, fstr), m_type, _fstr_to_regex(fstr))
        for m_type, (_dtype, dname, fstr) in PUBLIC_RECORD_TYPES.items()
    ),
    key=lambda t: len(t[0]),
    reverse=True,
)
LOG.debug(f'_RELPATH_TO_METADATA: {_RELPATH_TO_METADATA}')


def path_to_metadata(path: Path, rec_dir: Path) -> r.PublicRecordMetadata:
    "Wrapper for when you want metadata from a path that includes the records dir."
    LOG_CALL()
    LOG.debug(f'abspath: {abspath}')
    LOG.debug(f'rec_dir: {rec_dir}')
    relpath = Path(abspath).relative_to(Path(rec_dir)).with_suffix('')
    LOG.debug(f'relpath: {relpath}')
    return relpath_to_metdata(relpath)


def relpath_to_metadata(relpath: RecordMetadataRelPath) -> r.PublicRecordMetadata:
    "Inverse of metadata_to_relpath: decode a relative json file path back to metadata."
    # TODO append .json if not given?
    LOG_CALL()
    if not isinstance(relpath, Path):
        relpath = Path(relpath)
    LOG.debug(f'relpath: {relpath}')
    rel_str = relpath.as_posix()
    LOG.debug(f'rel_str: {rel_str}')
    fname = relpath.name  # filename only, folder stripped
    LOG.debug(f'fname: {fname}')

    for key, m_type, rx in _RELPATH_TO_METADATA:
        if not rel_str.startswith(key):
            continue
        m = rx.match(fname)
        if bool(m):
            LOG.debug(f'{fname} matches {rx} for type {m_type}')
        else:
            LOG.debug(f'{fname} does not match {rx} for type {m_type}')
        if not m:
            raise ValueError(
                f'Path matches {key!r} but not filename pattern: {abspath}'
            )
        LOG.debug(f'm.groupdict: {m.groupdict()}')
        return m_type(**m.groupdict())  # mixin coerces/validates
    raise ValueError(f'No record type matches path: {abspath}')


def load_all_guardian_pubkeys(n_guardians: int, store: RecordStore):
    "Load all guardian pubkeys, or raise an error if any are missing."
    LOG_CALL()
    LOG.debug(f'n_guardians: {n_guardians}')
    # pub_dir = Path(pub_dir)
    # LOG.debug(f'pub_dir: {pub_dir}')
    records = []
    for i in range(1, n_guardians+1):
        m = r.GuardianPubkey(guardian_number=i)
        LOG.debug(f'm: {m}')
        rec = store.load_verified_record_by_metadata(m)
        LOG.debug(f'loaded rec: {rec}')
        records.append(rec)
    return records


def key_ceremony_round1_complete(store: RecordStore):
    LOG_CALL()
    try:
        # details = load_record(r.CeremonyDetails(), pub_dir)
        m = r.CeremonyDetails()
        details = store.load_verified_record_by_metadata(m)
        LOG.debug(f'details: {details}')
        n = details.number_of_guardians
        LOG.debug(f'n guardians: {n}')
        # TODO prevent guardians from gaming this by posting an extra key
        pubkeys = load_all_guardian_pubkeys(n, store)
        LOG.debug(f'actual n_pubkeys: {len(pubkeys)}')
        return len(pubkeys) == n
    except Exception as e:
        LOG.error(e)
        return False


def key_ceremony_round2_complete(store: RecordStore):
    LOG_CALL()
    try:
        m = r.CeremonyDetails()
        # details = load_record(m, pub_dir)
        details = store.load_verified_record_by_metdata(m)
        LOG.debug(f'details: {details}')
        n = details.number_of_guardians
        LOG.debug(f'n guardians: {n}')
        # TODO prevent guardians from gaming this by posting extra backups
        n_backups_expected = n**2 - n
        LOG.debug(f'n_backups_expected: {n_backups_expected}')
        backups = load_all_guardian_backups(n, store)
        LOG.debug(f'actual n_backups: {len(backups)}')
        return len(backups) == n_backups_expected
    except Exception as e:
        LOG.error(e)
        return False


# TODO where should this live?
def load_all_guardian_backups(n_guardians: int, store: RecordStore):
    "Load all guardian backups, or raise an error if any are missing."
    LOG_CALL()
    LOG.debug(f'n_guardians: {n_guardians}')
    records = []
    for guardian_number in range(1, n_guardians+1):
        for backup_order in range(1, n_guardians+1):
            if guardian_number == backup_order:
                LOG.debug(f'skip guardian_number {guardian_number} backup {backup_order}')
                continue # guardians don't send themselves a backup
            m = r.GuardianBackup(
                guardian_number = guardian_number,
                backup_order    = backup_order
            ),
            LOG.debug(f'm: {m}')
            # rec = load_record(pub_dir)
            rec = store.load_verified_record_by_metadata(m)
            LOG.debug(f'loaded rec: {rec}')
            records.append(rec)
    return records


# def record_key(record) -> RecordMetadataRelPath:
#     "Work around record `unhashable type` issues."
#     # TODO use relative path from the records dir instead?
#     # TODO add a method to the dataclass instead?
#     # TODO use entire record including cid for key? seems more secure, but not always known?
#     LOG_CALL()
#     return str(record.metadata)


class VerifiedPostingMismatchError(Exception):
    "One or more verified paths have different content than their to-post equivalents."

    def __init__(self, mismatches: list[Path]):
        self.mismatches = mismatches
        super().__init__(f"{len(mismatches)} mismatch(es): {mismatches}")


def _hash(path: Path, chunk=64*1024) -> str:
    LOG_CALL()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


# TODO record state enum here? might be good for the interface


class RecordStore:
    """Manages fetching and verifying records. All save and load operations
    should go through this rather than reading or writing files directly.
    Various other objects should keep references to it for record related queries."""

    def __init__(
            self,
            records_posting_dir : Path,
            records_rejected_dir: Path,
            records_verified_dir: Path,
        ):
        LOG_CALL()

        self.records_posting_dir : Path = records_posting_dir
        self.records_rejected_dir: Path = records_rejected_dir
        self.records_verified_dir: Path = records_verified_dir

        # ensure record dirs exist and are empty
        for d in [records_posting_dir, records_rejected_dir, records_verified_dir]:
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True, exist_ok=False)

        # All records seen so far, except the rejected ones.
        # (These need to be excluded to keep the keys unique)
        self._records_on_chain: dict[RecordMetadataRelPath, r.PublicRecord] = {}

        # TODO _records_posting? not needed for now

        # Records which have been seen on chain, but whose data has not been successfully fetched.
        # More info about the number of attempts etc should be available from the IPFSService.
        self._records_pending_fetch: set[RecordMetadataRelPath] = set()

        # Records whose data have been fetched but not verified yet.
        # They may have just not been looked at yet, or they may be waiting for
        # an unfetched dependency. More info available from the Verifier.
        # TODO also reject if the election/phase ends with the dep still missing?
        self._records_pending_verify: set[RecordMetadataRelPath] = set()

        # Records successfully verified.
        self._records_verified: set[RecordMetadataRelPath] = set()

        # Records definitively rejected, in no particular order for now.
        # They can't be kept as a set of keys because those keys aren't reliable and could overlap.
        # TODO organize by who posted them for disputes: dict[ChannelId, list[r.PublicRecord]]
        self._records_rejected: list[r.PublicRecord] = []

    def key_for_record(self, record: r.PublicRecord):
        LOG_CALL()
        return metadata_to_relpath(record.metadata)

    def record_for_key(self, key: str):
        LOG_CALL()
        return self._records_on_chain[key]

    def record_seen_on_chain(self, record):
        """Called by Subscriber in response to a record being posted on chain.
        Should only be called once if the event filtering is working properly
        and there are no rollbacks, but idempotent just in case.
        """
        # TODO what should happen to the RecordStore state on rollbacks?
        LOG_CALL()
        key = self.key_for_record(record)
        LOG.debug(f'key: {key}')
        if key in self._records_on_chain:
            LOG.info(f'ignoring duplicate record: {record}')
        else:
            LOG.info(f'add {record}')
            self._records_on_chain[key] = record
            self._records_pending_fetch.add(key)

    def cid_data_fetched(self, cid, data: bytes):
        """Called by IPFSService after a successful fetch. Implies the data
        matches the CID and is ready to be parsed + verified + written to disk."""
        # key = self.key_for_record(cid)
        LOG_CALL()
        cid_str = ipfs_cid_to_string(cid)
        # there may be more than one record per cid, so make a list first
        records_fetched = [
            (k, r)
            for (k, r) in self._records_on_chain.items()
            if ipfs_cid_to_string(r.ipfs_cid) == cid_str # TODO use cid equality directly?
        ]

        # Move from pending fetch -> pending verification first
        for (key, _) in records_fetched:
            LOG.debug(f'move {key}: pending fetch -> pending verify')
            self._records_pending_verify.add(key)
            self._records_pending_fetch.remove(key)

        # Then attempt to do the verification. Some may have to wait because
        # they have unfetched dependenecies.
        # TODO verification here (loop, or separate fn?)
        records_verified = records_fetched

        self._save_verified_records(data, records_verified)
        # TODO also save records that fail verfification, but flag them

    def count_unverified_records(self, records=[]):
        """A bit like IPFSService.count_pending_cids, except:
        - does not count pending CIDs for other records not passed as an arg
        - counts records not yet seen on chain
        - returns the number of records with unverified data, not unverified CIDs
        If not given any records, defaults to all of them.
        """
        LOG_CALL()
        if not records:
            records = list(self._records_on_chain.values())
        keys = [self.key_for_record(r) for r in records]
        unverified   = [k for k in keys if not k in self._records_verified]
        n            = len(records)
        n_unverified = len(unverified)
        n_verified   = n - len(unverified)
        LOG.info(f'{n_verified}/{n} records verified, leaving {n_unverified} unverified: {unverified}')
        return n_unverified

    def _save_verified_records(self, data, kr_pairs):
        "Multi-record version because a given CID may match more than one."
        LOG_CALL()
        LOG.debug(f'saving {len(kr_pairs)} verified records: {kr_pairs}')
        for (key, record) in kr_pairs:
            self._save_verified_record(data, record)
            LOG.debug(f'move {key}: _records_pending_fetch -> _records_verified')
            self._records_verified.add(key)
            self._records_pending_verify.remove(key)

        # This may also remove other now-verified records.
        # It just seems like a reasonable place to trigger it.
        removed = self._rm_records_posted()
        if removed:
            LOG.info(f'removed now-verified files from posting dir: {removed}')

        # TODO also look for pending verifications that can now continue here

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
            LOG.info(f'saved verified {record.metadata} -> {save_path}')
            return save_path
        finally:
            # Clean up the temp file if anything failed before the replace
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass

    def _rm_records_posted(self) -> list[Path]:
        """Delete files in records_posting_dir that also exist in
        records_verified_dir with identical relative path + content.

        After processing everything, raises VerifiedPostingMismatchError if any
        shared relative path had differing content. Returns removed rel paths.

        The idea is to keep the posting dir clean of extra JSON files, but also
        never accidentally delete something in process.

        This should NOT remove posting files which match rejected records,
        because the same data can be rejected in one case but valid in another,
        depending on the metadata. The rejected files will be left in the
        posting dir for now, which should be helpful for forensics.
        """
        LOG_CALL()
        removed, mismatches = [], []
        for post_file in self.records_posting_dir.rglob("*"):
            if not post_file.is_file():
                continue
            rel = post_file.relative_to(self.records_posting_dir)
            fetched_file = self.records_verified_dir / rel
            if not fetched_file.is_file():
                continue

            if (post_file.stat().st_size == fetched_file.stat().st_size
                    and _hash(post_file) == _hash(fetched_file)):
                post_file.unlink()
                removed.append(rel)
            else:
                mismatches.append(rel)
        if mismatches:
            raise VerifiedPostingMismatchError(mismatches)
        return removed


    def load_verified_record_by_metadata(metadata: r.PublicRecordMetadata):
        """Given PublicRecordMetadata, load the corresponding record object.
        Handles decoding, and implicitly verification (by using the verified dir).
        """
        LOG_CALL()
        if isinstance(metadata, r.PublicRecord):
            LOG.warning(f'Passed PublicRecord rather than PublicRecordMetadata: {metadata}')
            metadata = metadata.metadata
        mtype = type(metadata)
        LOG.debug(f'mtype: {mtype}')
        (decode_cls, _, _) = PUBLIC_RECORD_TYPES[mtype]
        LOG.debug(f'decode_cls: {decode_cls}')
        # path = record_path(metadata, pub_dir)
        path = metadata_to_path(metadata, self.records_verified_dir)
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

    def load_verified_record_by_relpath(relpath: Path):
        """Given a relative path, load the corresponding verified record
        object. I mostly envision this being useful for the CLI so users can
        autocomplete the path rather than trying to type out the metdata
        format. It could also be used to load from various key sets.
        """
        # TODO CLI needs to remove the verified dir prefix, then this will re add it?
        LOG_CALL()
        LOG.debug(f'relpath: {relpath}')
        metadata = relpath_to_metadata(relpath)
        LOG.debug(f'metadata: {metadata}')
        return self.load_verified_record_by_metadata(metadata)
