from .code import STATIC_PHASES
from .code import STATIC_TRANSACTIONS
from egc import *

import json
from pathlib import Path

import logging


LOG = logging.getLogger(__name__)


STATIC_FILES_DIR = Path(__file__).absolute().parent / 'files'


def load_static_record_pair(
        record: PublicRecord
    ) -> tuple[dict, PublicRecordMetadata]:
    mdata = record.metadata
    path = record_path(mdata, STATIC_FILES_DIR)
    with open(path, 'r') as f:
        obj = json.load(f)
    return (obj, mdata)


def load_static_record_pairs(
        records: list[PublicRecord],
    ) -> list[tuple[dict, PublicRecordMetadata]]:
    LOG.debug('load_static_record_pairs')
    pairs = []
    for rec in records:
        LOG.debug(f'rec: {rec}')
        pair = load_static_record_pair(rec)
        pairs.append(pair)
    return pairs
