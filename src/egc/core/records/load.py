from ..plutus.types import record as r
from ..utils import make_log_call
from .paths import *
from .store import *

import logging
LOG = logging.getLogger(__name__)
LOG_CALL = make_log_call(LOG.debug)


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
        details = store.load_verified_record_by_metadata(m)
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


