from pathlib import Path

import electionguard as eg
import hashlib
import os
import shutil
import tempfile
import json

from ..plutus import IpfsCid, ipfs_cid_to_string
from ..plutus.types import record as r
from ..utils import make_log_call
from .paths import *

import logging
LOG = logging.getLogger(__name__)
LOG_CALL = make_log_call(LOG.debug)


class VerifiedPostingMismatchError(Exception):
    "One or more verified paths have different content than their to-post equivalents."

    def __init__(self, mismatches: list[Path]):
        self.mismatches = mismatches
        super().__init__(f"{len(mismatches)} mismatch(es): {mismatches}")


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
            leave_existing_files = False, # Set True to avoid clobbering existing files you're confident in
        ):
        LOG_CALL()

        self.records_posting_dir : Path = records_posting_dir
        self.records_rejected_dir: Path = records_rejected_dir
        self.records_verified_dir: Path = records_verified_dir

        # ensure record dirs exist and are empty
        for d in [records_posting_dir, records_rejected_dir, records_verified_dir]:
            if not isinstance(d, Path):
                d = Path(d)
            if leave_existing_files:
                d.mkdir(parents=True, exist_ok=True)
            else:
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir(parents=True, exist_ok=False)

        # All records seen so far, except the rejected ones.
        # (These need to be excluded to keep the keys unique)
        self._records_on_chain: dict[RecordMetadataRelPath, r.PublicRecord] = {}

        # For skipping fetch of any records with duplicate CIDs,
        # so the _records_pending_fetch doesn't accumulate anything.
        # TODO is this really helpfuL?
        self._cids_fetched: set[IpfsCid] = set()

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
            if record.ipfs_cid in self._cids_fetched:
                LOG.info(f'skip fetching duplicate CID: {record}')
            else:
                self._records_pending_fetch.add(key)

    def cid_data_fetched(self, cid, data: bytes):
        """Called by IPFSService after a successful fetch. Implies the data
        matches the CID and is ready to be parsed + verified + written to disk."""
        # key = self.key_for_record(cid)
        LOG_CALL()
        self._cids_fetched.add(cid)
        cid_str = ipfs_cid_to_string(cid)
        # there may be more than one record per cid, so make a list first
        records_fetched = [
            (k, r)
            for (k, r) in self._records_pending_fetch.items()
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
        # TODO remove fn in favor of a simple loop?
        LOG_CALL()
        LOG.debug(f'saving {len(kr_pairs)} verified records: {kr_pairs}')
        for (key, record) in kr_pairs:
            self._save_verified_record(data, record)

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
        key = self.key_for_record(record)
        save_path = metadata_to_path(record.metadata, self.records_verified_dir)
        LOG.debug(f'save_path: {save_path}')
        cid_str = ipfs_cid_to_string(record.ipfs_cid)
        LOG.debug(f'cid_str: {cid_str}')
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # It seems to be essential to use the same filesystem here to avoid
        # "invalid cross-device link".
        fd, tmp_path = tempfile.mkstemp(dir=save_path.parent, suffix=".json.part")

        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, save_path)
            LOG.info(f'saved verified {record.metadata} -> {save_path}')
            LOG.debug(f'move {key}: pending verify -> verified')
            self._records_verified.add(key)
            self._records_pending_verify.remove(key)
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

        def _hash(path: Path, chunk=64*1024) -> str:
            LOG_CALL()
            h = hashlib.sha256()
            with path.open("rb") as f:
                for block in iter(lambda: f.read(chunk), b""):
                    h.update(block)
            return h.hexdigest()

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


    def load_verified_record_by_metadata(self, metadata: r.PublicRecordMetadata):
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
                # LOG.debug(f'data without regular serialization:\n\n{txt}\n')
                data = json.loads(txt)
                if decode_cls != dict:
                    try:
                        data = decode_cls(**data)
                        LOG.debug(f'decoded using {decode_cls} kwargs')
                    except:
                        LOG.debug('decoded with json.loads only')
                else:
                    LOG.debug('decoded with json.loads only')

        LOG.debug(f'decoded data: {data}')
        assert type(data) == decode_cls
        return data

    def load_verified_record_by_relpath(relpath: RecordMetadataRelPath):
        """Given a relative path, load the corresponding verified record
        object. I mostly envision this being useful for the CLI so users can
        autocomplete the path rather than trying to type out the metdata
        format. It could also be used to load from various key sets.
        """
        # TODO CLI needs to remove the verified dir prefix, then this will re add it?
        # TODO catch relative paths here?
        LOG_CALL()
        LOG.debug(f'relpath: {relpath}')
        metadata = relpath_to_metadata(relpath)
        LOG.debug(f'metadata: {metadata}')
        return self.load_verified_record_by_metadata(metadata)


    def save_record_to_posting_dir(metadata: r.PublicRecordMetadata, obj: Any) -> Path:
        "Save a new record in the posting dir and return its path."
        relpath = metadata_to_relpath(metadata)
        LOG.debug(f'metadata: {metadata}')
        path = self.records_posting_dir / relpath
        LOG.debug(f'path: {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        # TODO use my fancy_dumps or similar here?
        # with open(fpath, 'w') as f:
            # json.dump(obj, f)
        txt = eg.serialize.to_raw(obj) # TODO helper fn? will this fail on the couple odd ones?
        LOG.debug(f'raw txt: {txt}')
        path.write_text(txt)
        LOG.info(f'Saved {metadata} -> {path}')
        return path
