import pytest
import json
import electionguard as eg
from egc import EgcManifest, EgcContest
from hypothesis import given, settings
from hypothesis import strategies as st
from ..lib.example_data import EXAMPLE_CONTESTS
from ..lib.json_utils import assert_json_roundtrip

import logging
LOG = logging.getLogger(__name__)

@given(contests = st.lists(
    st.sampled_from(EXAMPLE_CONTESTS),
    unique_by = lambda c: c['question'])
)
@settings(max_examples = 1_000)
def test_roundtrip_manifest_to_json(contests: list[dict]):
    egc_manifest = EgcManifest(
        contests = [EgcContest.from_cfg_dict(c) for c in contests]
    )
    assert_json_roundtrip(egc_manifest)

@given(contests = st.lists(
    st.sampled_from(EXAMPLE_CONTESTS),
    unique_by = lambda c: c['question'])
)
@settings(max_examples = 1_000)
def test_validate_manifest_json(contests: list[dict]):
    egc_manifest = EgcManifest(
        contests = [EgcContest.from_cfg_dict(c) for c in contests]
    )
    eg_json_str = json.dumps( egc_manifest.to_eg_dict() )
    eg_manifest = eg.serialize.from_raw(eg.Manifest, eg_json_str)
    assert isinstance(eg_manifest, eg.Manifest)
    assert eg_manifest.is_valid()
