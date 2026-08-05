from .plutus import *
import logging
from typing import Any
from pathlib import Path
from electionguard import serialize as eg_serialize


LOG = logging.getLogger(__name__)


# metadata type : (dir relname, basename fmtargs ptn)
# TODO put back electionguard types when needed
# TODO any use for the old "record type strings"? remove if not
PUBLIC_RECORD_TYPES = {
    Manifest: (
        # 'manifest'
        # Manifest,
        '1_config/1_announce',
        '1_manifest'
    ),
    CeremonyDetails: (
        # 'ceremony_details'
        # CeremonyDetails,
        '1_config/1_announce',
        '2_ceremony'
    ),
    GuardianPubkey: (
        # 'guardian_pubkey'
        # ElectionPublicKey,
        '1_config/2_ceremony/1_pubkeys',
        'guardian_{guardian_number}'
    ),
    GuardianBackup: (
        # 'guardian_backup'
        # ElectionPartialKeyBackup,
        '1_config/2_ceremony/2_backups',
        'guardian_{guardian_number}_backup_{backup_order}'
    ),
    GuardianVerification: (
        # 'guardian_verification'
        # ElectionPartialKeyVerification,
        '1_config/2_ceremony/3_verifications',
        'guardian_{guardian_number}_backup_{backup_order}'
    ),
    JointKey: (
        # 'joint_key'
        # ElectionJointKey,
        '1_config/3_election',
        'joint_key'
    ),
    Constants: (
        # 'constants'
        # ElectionConstants,
        '1_config/3_election',
        'constants'
    ),
    Context: (
        # 'context'
        # CiphertextElectionContext,
        '1_config/3_election',
        'context'
    ),
    Device: (
        # 'device'
        # EncryptionDevice,
        '1_config/4_devices',
        'device_{device_number}'
    ),
    BallotSubmitted: (
        # 'ballot_submitted'
        # CiphertextBallot, # TODO SubmittedBallot with state set to UNKNOWN?
        '2_ballots/1_submitted',
        '{ballot_id}'
    ),
    CastNotice: (
        # 'cast_notice'
        # CastNotice,
        '2_ballots/2_cast',
        '{ballot_id}'
    ),
    BallotSpoiled: (
        # 'ballot_spoiled'

        # This seems correct to me even though it doesn't match the
        # electionguard-python implementation: we *do* want to publish all
        # the nonces at this step, right? So people can decrypt immediately
        # rather than waiting for the guardians.
        # CiphertextBallot,

        '2_ballots/3_spoiled',
        '{ballot_id}'
    ),
    CiphertextTally: (
        # 'ciphertext_tally'
        # PublishedCiphertextTally, # TODO CiphertextTally? (the non-"published" version)
        '3_results',
        '1_tally'
    ),
    TallyShare: (
        # 'tally_share'
        # DecryptionShare,
        '3_results/2_decrypt/1_shares/1_tally',
        'tally_guardian_{guardian_number}'
    ),
    SpoiledShare: (
        # 'spoiled_share'
        # DecryptionShare,
        '3_results/2_decrypt/1_shares/2_spoiled',
        '{spoiled_id}_guardian_{guardian_number}'
    ),
    # TODO rename tally_result?
    PlaintextTally: (
        # 'plaintext_tally'
        # PlaintextTally,
        '3_results/2_decrypt/2_combined',
        '1_tally'
    ),
    SpoiledResult: (
        # 'spoiled_result'
        # PlaintextTally,
        '3_results/2_decrypt/2_combined/2_spoiled',
        '{ballot_id}'
    ),
    Summary: (
        # 'summary'
        # dict,
        '4_verify',
        '{verifier_id}'
    ),
}


def record_path(metadata: PublicRecordMetadata, pub_dir: Path) -> Path:
    "Find the path of a record in the public records dir by metadata."
    LOG.debug(f'metadata: {metadata}')
    if isinstance(metadata, PublicRecord):
        LOG.warning(f'Passed PublicRecord rather than PublicRecordMetadata: {metadata}')
        metadata = metadata.metadata
    if not isinstance(pub_dir, Path):
        pub_dir = Path(pub_dir)
    m_type = type(metadata)
    LOG.debug(f'm_type: {m_type}')
    (dname, fstr) = PUBLIC_RECORD_TYPES[m_type]
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
def save_record(metadata: PublicRecordMetadata, obj: Any, pub_dir: Path) -> Path:
    "Save a PublicRecord in the public records dir and return its path."
    fpath = record_path(metadata, pub_dir=pub_dir)
    fpath.parent.mkdir(parents=True, exist_ok=True)

    # TODO use my fancy_dumps or similar here?
    # with open(fpath, 'w') as f:
        # json.dump(obj, f)
    fpath.write_text( eg_serialize.to_raw(obj) )

    LOG.info(f'Saved {record} -> {fpath}')
    return fpath


# TODO any way to type this reasonably?
# TODO is this needed yet?
# def load_record(record: PublicRecord, root_dir: Path) -> Optional[Any]:
#     pass
