from egc import *
import tempfile

import logging
LOG = logging.getLogger(__name__)

def load_static_record_pair(
        record: PublicRecord,
        store: RecordStore,
    ) -> tuple[dict, PublicRecordMetadata]:
    mdata = record.metadata
    obj = store.load_verified_record_by_metadata(mdata)
    return (obj, mdata)

def load_static_record_pairs(
        records: list[PublicRecord],
        store: RecordStore,
    ) -> list[tuple[dict, PublicRecordMetadata]]:
    LOG.debug('load_static_record_pairs')
    pairs = []
    for rec in records:
        LOG.debug(f'rec: {rec}')
        pair = load_static_record_pair(rec, store)
        pairs.append(pair)
    return pairs

def fixture_private_dir(root, req):
    "For giving each fixture and individual private_dir for ipfs etc."
    return root / req.node.path.stem / req.fixturename
