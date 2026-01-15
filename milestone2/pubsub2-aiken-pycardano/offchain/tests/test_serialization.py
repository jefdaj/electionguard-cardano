from os.path import exists
from pathlib import Path
from typing import Dict

def test_load_election_records(election_records: Dict[Path, bytes]):
    assert isinstance(election_records, Dict)
    assert all(
        isinstance(k, Path) and isinstance(v, bytes) # CIDv1 == bytes
        for k, v in election_records.items()
    )
    assert all(
        exists(k) for k in election_records.keys()
    )
