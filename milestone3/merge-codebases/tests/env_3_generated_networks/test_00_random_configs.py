

def assert_json_roundtrip(cfg):
    tmp  = json.dumps(cfg)
    cfg2 = json.loads(tmp)
    assert cfg == cfg2

@given(cfg=voteconfig())
@settings(max_examples=1_000)
def test_json_voteconfig(cfg: VoteConfig):
    assert_json_roundtrip(cfg)

@given(cfg=contestconfig())
@settings(max_examples=1_000)
def test_json_contestconfig(cfg: ContestConfig):
    assert_json_roundtrip(cfg)

@given(cfg=electionconfig())
@settings(max_examples=1_000)
def test_json_electionconfig(cfg: ElectionConfig):
    assert_json_roundtrip(cfg)

# @given(cfg=attackconfig())
# @settings(max_examples=1_000)
# def test_json_attackcfg(cfg: AttackConfig):
#     assert_json_roundtrip(cfg)

@given(cfg=honestrun())
@settings(max_examples=1_000)
def test_json_honestrun(cfg: RunConfig):
    assert_json_roundtrip(cfg)

# @given(cfg=attackrun())
# @settings(max_examples=1_000)
# def test_json_attackrun(cfg: RunConfig):
#     assert_json_roundtrip(cfg)
