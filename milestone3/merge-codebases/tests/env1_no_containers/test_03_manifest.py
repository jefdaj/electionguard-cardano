import pytest
from egc import *
from hypothesis import given, settings
from hypothesis import strategies as st
from ..lib.example_data import EXAMPLE_CONTESTS
from ..lib.json_utils import assert_json_roundtrip

import logging
LOG = logging.getLogger(__name__)

@given(contests = st.sampled_from(EXAMPLE_CONTESTS))
@settings(max_examples = 100)
def test_roundtrip_manifest(contests: list[dict]):
    manifest = EgcManifest(
        contests = [EgcContest.from_cfg_dict(c) for c in contests]
    )
    assert_json_roundtrip(manifest)
