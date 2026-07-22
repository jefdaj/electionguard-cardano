from egc import *

import logging
LOG = logging.getLogger(__name__)

def load_static_record_pair(
        record: PublicRecord,
        static_files_dir,
    ) -> tuple[dict, PublicRecordMetadata]:
    mdata = record.metadata
    path = record_path(mdata, static_files_dir)
    with open(path, 'r') as f:
        obj = json.load(f)
    return (obj, mdata)

def load_static_record_pairs(
        records: list[PublicRecord],
        static_dir,
    ) -> list[tuple[dict, PublicRecordMetadata]]:
    LOG.debug('load_static_record_pairs')
    pairs = []
    for rec in records:
        LOG.debug(f'rec: {rec}')
        pair = load_static_record_pair(rec, static_dir)
        pairs.append(pair)
    return pairs
