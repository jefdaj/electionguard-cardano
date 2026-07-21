from hypothesis import given, settings
from hypothesis.strategies import composite
from tests.env_3_generated_networks.helpers import *

# Honest/clean election (no attacks)
@composite
def honestrun(draw):
    arion_cfg    = arionconfig()
    election_cfg = draw(electionconfig())
    votes_cfg    = draw(contestsconfig())
    cfg = RunJson(
        arion_cfg=arion_cfg,
        election_cfg=election_cfg,
        votes_cfg=votes_cfg,
        attack_cfg=[] # only difference from attack version
    )
    return cfg

@given(cfg=honestrun())
@settings(max_examples=1_000)
def test_json_honestrun(cfg: RunJson):
    assert_json_roundtrip(cfg)
