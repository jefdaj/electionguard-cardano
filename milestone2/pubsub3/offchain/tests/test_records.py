import pytest
from pubsub import *
from .conftest import *

def test_load_election_records(election_records: ElectionRecords):
    assert isinstance(election_records, List)
    assert all(
        isinstance(k, Path) and isinstance(v, CID)
        for (k, v) in election_records
    )
    assert all(
        exists(k) for (k, v) in election_records
    )
