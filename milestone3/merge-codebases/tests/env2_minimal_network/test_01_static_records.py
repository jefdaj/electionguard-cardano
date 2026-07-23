import json
import pytest
from .lib import load_static_record_pairs
from egc import *

import logging
from pathlib import Path
from typing import Tuple
from pprint import pprint

# These are technically offline tests, but I put them in the 2_minimal_networks
# section because they're just verifying the static record handling that will
# be used in the happy_subchannels and happy_election tests.

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

def test_load_static_record_pairs(static_records_list, static_files_dir):
    pairs = load_static_record_pairs(static_records_list, static_files_dir)
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

def test_roundtrip_static_records_to_str(
        static_records_list: list[PublicRecord],
    ):
    for rec in static_records_list:
        # PyCardano uses repr() for JSON, which is a little suprising in Python
        # but reasonable for comparing with cardano-cli etc. So we round-trip
        # to str instead.
        tmp  = str(rec)
        rec2 = eval(tmp)
        assert rec2 == rec
