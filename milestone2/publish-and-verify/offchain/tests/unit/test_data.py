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

def test_load_static_phases(static_phases: dict[int, ElectionPhase]):
    assert len(static_phases) == 8
    assert all(
        isinstance(k, int) and isinstance(v, ElectionPhase)
        for (k, v) in static_phases.items()
    )

def test_load_static_transactions(
        static_transactions: dict[str, dict[int, Tuple[ElectionAction, list[PublicRecord]]]]
    ):
    assert len(static_transactions) == 6
    for (channel_str, tx_dict) in static_transactions.items():
        assert isinstance(channel_str, str)
        for (seq, (act, recs)) in tx_dict.items():
            assert isinstance(seq, int)
            assert isinstance(act, ElectionAction)
            for rec in recs:
                assert isinstance(rec, PublicRecord)
