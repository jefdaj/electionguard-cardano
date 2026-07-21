from hypothesis import given, settings, composite
from helpers_env3 import assert_json_roundtrip

@given(cfg=honestrun())
@settings(max_examples=1_000)
def test_json_honestrun(cfg: RunConfig):
    assert_json_roundtrip(cfg)

# Honest/clean election (no attacks)
@composite
def honestrun(draw):
    arion_cfg    = arionconfig()
    election_cfg = draw(electionconfig())
    votes_cfg    = draw(contestsconfig())
    cfg = RunConfig(
        arion_cfg=arion_cfg,
        election_cfg=election_cfg,
        votes_cfg=votes_cfg,
        attack_cfg=[] # only difference from attack version
    )
    return cfg
