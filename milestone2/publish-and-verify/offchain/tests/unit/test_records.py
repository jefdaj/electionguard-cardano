import json
import pytest
from egc import *
import logging
from pathlib import Path
from typing import Tuple
from pprint import pprint

LOG = logging.getLogger(__name__)

@pytest.mark.local
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
