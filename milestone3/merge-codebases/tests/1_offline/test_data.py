import json
import pytest
from egc import *

# TODO why is this needed?
from fixtures.data import *

import logging
from pathlib import Path
from typing import Tuple
from pprint import pprint

LOG = logging.getLogger(__name__)

def test_load_static_phases(
        static_phases: dict[int, ElectionPhase],
    ):
    assert len(static_phases) == 8
    assert all(
        isinstance(k, int) and isinstance(v, ElectionPhase)
        for (k, v) in static_phases.items()
    )

def test_load_static_transactions(
        static_transactions: dict[str, dict[int, Tuple[ElectionAction, list[PublicRecord]]]],
    ):
    assert len(static_transactions) == 6
    for (channel_str, tx_dict) in static_transactions.items():
        assert isinstance(channel_str, str)
        for (seq, (act, recs)) in tx_dict.items():
            assert isinstance(seq, int)
            assert isinstance(act, ElectionAction)
            assert isinstance(recs, list)
            for rec in recs:
                assert isinstance(rec, PublicRecord)

# TODO why not just make the pairs a fixture?
def test_load_static_record_pairs(
        static_records_list: list[PublicRecord],
    ):

    pairs = load_static_record_pairs(static_records_list)

    assert len(static_records_list) == 78
    assert len(pairs) == 78

    cid_strs = set()

    for (rec, (obj, mdata)) in zip(static_records_list, pairs):
        cid_str = ipfs_cid_to_string(rec.ipfs_cid)
        cid_strs.add(cid_str)
        assert isinstance(rec, PublicRecord)
        assert isinstance(obj, dict)
        assert isinstance(mdata, PublicRecordMetadata)

    # There are 78 records, but the 5 verifications all have the same
    # CID because they agree exactly.
    assert len(cid_strs) == 74
