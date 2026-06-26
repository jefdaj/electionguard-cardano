from .code import STATIC_PHASES
from .code import STATIC_TRANSACTIONS
from egc import PublicRecord, PublicRecordMetadata, ipfs_cid_to_string

import json
from pathlib import Path

import logging


LOG = logging.getLogger(__name__)


# TODO is absolute the best choice here?
STATIC_FILES_DIR   = Path(__file__).absolute().parent / 'files'


def make_static_files_by_cid():
    cids_path  = Path(__file__).absolute().parent / 'file_cids.txt'
    files_path = Path(__file__).absolute().parent / 'file_paths.txt'
    cids  = cids_path.read_text().splitlines()
    paths = files_path.read_text().splitlines()
    paths = [STATIC_FILES_DIR / p for p in paths]
    return {c: p for (c, p) in zip(cids, paths)}


STATIC_FILES_BY_CID = make_static_files_by_cid()


def load_static_record_obj(cid: str) -> dict:
    path = STATIC_FILES_BY_CID[cid]
    with open(path, 'r') as f:
        return json.load(f)


def load_static_record_pairs(
        records: list[PublicRecord],
    ) -> list[tuple[dict, PublicRecordMetadata]]:
    LOG.debug('load_static_record_pairs')
    pairs = []
    for rec in records:
        LOG.debug(f'rec: {rec}')
        cid = ipfs_cid_to_string(rec.ipfs_cid)
        LOG.debug(f'cid: {cid}')
        obj = load_static_record_obj(cid)
        pair = (obj, rec.metadata)
        pairs.append(pair)
    return pairs
