import json
import pytest
from egc import *
import logging
from pathlib import Path
from typing import Tuple
from pprint import pprint

LOG = logging.getLogger(__name__)

@pytest.mark.local
def test_load_static_phases(
        static_phases: dict[int, ElectionPhase],
    ):
    assert len(static_phases) == 8
    assert all(
        isinstance(k, int) and isinstance(v, ElectionPhase)
        for (k, v) in static_phases.items()
    )

@pytest.mark.local
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

@pytest.mark.local
def test_load_static_files_by_cid(
        static_records_list: list[PublicRecord],
        static_files_by_cid: dict[str, Path],
    ):

    # There are 79 records, but the verifications all have the same
    # CID because they agree exactly.
    # TODO add something unique to prevent that?
    # TODO lean more on the reverse path -> cid lookup instead?
    assert len(static_records_list) == 79
    assert len(static_files_by_cid) == 75

    for rec in static_records_list:
        cid_str = ipfs_cid_to_string(rec.ipfs_cid)
        path = static_files_by_cid[cid_str]
        assert isinstance(path, Path)
        with path.open('r') as f:
            assert json.load(f)
