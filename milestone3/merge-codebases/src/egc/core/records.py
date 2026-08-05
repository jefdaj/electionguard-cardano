# from .plutus import *
from .plutus.types import record as r

import electionguard as eg

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
    if isinstance(metadata, PublicRecord):
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


# TODO any way to type this reasonably?
# TODO is this needed yet?
# def load_record(record: PublicRecord, root_dir: Path) -> Optional[Any]:
#     pass
