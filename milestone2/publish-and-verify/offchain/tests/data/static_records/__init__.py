from .code import STATIC_PHASES
from .code import STATIC_TRANSACTIONS

import json
from pathlib import Path

# TODO is absolute the best choice here?
STATIC_FILES_DIR = Path(__file__).absolute().parent / 'files'
STATIC_CIDS_JSON = Path(__file__).absolute().parent / 'cids.json'

STATIC_FILES_BY_CID: dict[str, Path] = {}

with STATIC_CIDS_JSON.open('r') as f:
    json_dict = json.load(f)
    for (filename, cid) in json_dict.items():
        path = STATIC_FILES_DIR / filename
        STATIC_FILES_BY_CID[cid] = path
