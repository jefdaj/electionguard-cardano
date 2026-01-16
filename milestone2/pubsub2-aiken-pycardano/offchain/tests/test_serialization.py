from os.path import exists
from pathlib import Path
from typing import List

def test_load_election_records(election_records: list[tuple[Path, bytes]]):
    assert isinstance(election_records, List)
    assert all(
        isinstance(k, Path) and isinstance(v, bytes) # CIDv1 == bytes
        for (k, v) in election_records
    )
    assert all(
        exists(k) for (k, v) in election_records
    )

# TODO test round-tripping PubsubAction types <--> CBOR
