from dataclasses import dataclass, asdict
from pathlib import PosixPath
from typing import Any

import electionguard as eg
import hashlib
import os
import random
import re
import shutil
import tempfile

from ..plutus import ipfs_cid_to_string
from ..plutus.types import record as r
from ..plutus.types import BallotId
from ..utils import make_log_call

import logging
LOG = logging.getLogger(__name__)
LOG_CALL = make_log_call(LOG.debug)


# Record metadata can be encoded to or decoded from a unique relative path
# using PUBLIC_RECORD_TYPES below. The path can be used as a hashable key for
# sets and dicts.
# TODO remove .json?
type RecordMetadataRelPath = str


# TODO remove? not sure cast_at adds anything since you can't trust the sender
@dataclass
class CastNotice:
    ballot_id: BallotId

    # timestamp, which should be in a window after ballot submitted
    cast_at: str

    def to_dict(self) -> dict:
        return asdict(self)


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
        CastNotice, # the one defined here
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


def metadata_to_path(metadata: r.PublicRecordMetadata, rec_dir: PosixPath) -> PosixPath:
    "Find the full path of a record in a records dir by metadata."
    LOG_CALL()
    relpath = metadata_to_relpath(metadata)
    if not isinstance(rec_dir, PosixPath):
        rec_dir = PosixPath(rec_dir)
    path = (rec_dir / relpath).with_suffix('.json')
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
    dname = PosixPath(dname)
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
    relpath = str((dname / fname).with_suffix('.json'))
    LOG.debug(f'relpath: {relpath}')
    return relpath


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


def path_to_metadata(path: PosixPath, rec_dir: PosixPath) -> r.PublicRecordMetadata:
    "Wrapper for when you want metadata from a path that includes the records dir."
    LOG_CALL()
    LOG.debug(f'path: {path}')
    LOG.debug(f'rec_dir: {rec_dir}')
    relpath = PosixPath(path).relative_to(PosixPath(rec_dir))# .with_suffix('.json')
    LOG.debug(f'relpath: {relpath}')
    return relpath_to_metdata(relpath)


def relpath_to_metadata(relpath: RecordMetadataRelPath) -> r.PublicRecordMetadata:
    "Inverse of metadata_to_relpath: decode a relative json file path back to metadata."
    # TODO append .json if not given?
    LOG_CALL()
    if not isinstance(relpath, PosixPath):
        relpath = PosixPath(relpath)
    LOG.debug(f'relpath: {relpath}')
    rel_str = relpath.as_posix().with_suffix('.json')
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
                f'PosixPath matches {key!r} but not filename pattern: {abspath}'
            )
        LOG.debug(f'm.groupdict: {m.groupdict()}')
        return m_type(**m.groupdict())  # mixin coerces/validates
    raise ValueError(f'No record type matches path: {abspath}')


