from .code import STATIC_PHASES
from .code import STATIC_TRANSACTIONS

import json

# TODO is absolute the best choice here?
STATIC_FILES_DIR = Path(__file__).absolute() / 'files'

STATIC_FILES_BY_CID: dict[str, Path] = {}
with Path(__file__).absolute().with_suffix('.json').open('r') as f:
    json_dict = json.load(f)
    for (filename, cid) in json_dict.items():
        path = STATIC_FILES_DIR / filename
        STATIC_FILES_BY_CID[cid] = path
