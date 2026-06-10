from .code import STATIC_PHASES
from .code import STATIC_TRANSACTIONS

import json
from pathlib import Path

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
