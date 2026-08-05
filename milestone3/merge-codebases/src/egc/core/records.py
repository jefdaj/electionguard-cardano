# from .plutus import *
from .plutus.types import record as r

import electionguard as eg

import re
import logging
from typing import Any
from pathlib import Path


LOG = logging.getLogger(__name__)


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

    LOG.info(f'Saved {record} -> {fpath}')
    return fpath


_FSTR_FIELD = re.compile(r'\{(\w+)\}')

# Optional: tighten groups only for intra-fstring disambiguation
# (multiple adjacent fields in one fstring). Not needed for uniqueness
# across types.
_FIELD_PATTERNS = {
    'ballot_id':       r'ballot-[0-9a-fA-F-]{36}',
    'spoiled_id':      r'ballot-[0-9a-fA-F-]{36}',
    'guardian_number': r'\d+',
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
    return f'{dname}/{fstr.split("{", 1)[0]}'


# Build once. Map unique (folder + literal prefix) -> (type, regex).
# Sort by key length descending so longer, more-specific prefixes win
# when one prefix is a substring-prefix of another sharing the folder.
_REVERSE = sorted(
    (
        (_key(dname, fstr), m_type, _fstr_to_regex(fstr))
        for m_type, (_dtype, dname, fstr) in PUBLIC_RECORD_TYPES.items()
    ),
    key=lambda t: len(t[0]),
    reverse=True,
)


def path_metadata(path: Path, pub_dir: Path) -> r.PublicRecordMetadata:
    "Inverse of record_path: decode a json file path back to metadata."
    LOG.debug(f'path: {path}')
    LOG.debug(f'pub_dir: {pub_dir}')
    rel = Path(path).relative_to(Path(pub_dir)).with_suffix('')
    LOG.debug(f'rel: {rel}')
    rel_str = rel.as_posix()
    LOG.debug(f'rel_str: {rel_str}')
    fname = rel.name  # filename only, folder stripped
    LOG.debug(f'fname: {fname}')

    for key, m_type, rx in _REVERSE:
        if not rel_str.startswith(key):
            continue
        m = rx.match(fname)
        if not m:
            raise ValueError(
                f'Path matches {key!r} but not filename pattern: {path}'
            )
        return m_type(**m.groupdict())  # mixin coerces/validates
    raise ValueError(f'No record type matches path: {path}')



# TODO load a record given the metadata (used by ipfs fetch)
