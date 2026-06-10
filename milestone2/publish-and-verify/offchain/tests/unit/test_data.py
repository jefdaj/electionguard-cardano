import pytest
from egc import *
import logging
from pprint import pprint

LOG = logging.getLogger(__name__)

# TODO make new fixtures for the static records
# TODO then reference that fixture from other tests
# TODO then write new round-trip tests here

# old test for reference:
# def test_load_election_records(election_records: ElectionRecords):
#     assert isinstance(election_records, List)
#     assert all(
#         isinstance(k, Path) and isinstance(v, CID)
#         for (k, v) in election_records
#     )
#     assert all(
#         exists(k) for (k, v) in election_records
#     )

def test_static_phases(static_phases):
    assert len(static_phases) == 8
    assert all(
        isinstance(k, int) and isinstance(v, ElectionPhase)
        for (k, v) in static_phases.items()
    )
