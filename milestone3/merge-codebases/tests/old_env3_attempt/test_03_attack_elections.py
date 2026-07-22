# TODO import from runconfig.py
# TODO and attacks.py?

# @given(cfg=attackconfig())
# @settings(max_examples=1_000)
# def test_json_attackcfg(cfg: AttackConfig):
#     assert_json_roundtrip(cfg)

# @given(cfg=attackrun())
# @settings(max_examples=1_000)
# def test_json_attackrun(cfg: RunConfig):
#     assert_json_roundtrip(cfg)


# @composite
# def attackconfig(draw, explicit_cfg=None):
#     if explicit_cfg is not None:
#         return explicit_cfg
#     attacks = draw(lists(
#         sampled_from(list(ATTACKS.keys())),
#         min_size=1,
#
#         # TODO how many would be useful? at least 3-4 right?
#         #      but only with enough examples to catch unusual combinations
#         max_size=2
#     ))
#     cfg = AttackConfig(attacks=attacks)
#     return cfg

# Messed up election with attacks
# @composite
# def attackrun(draw, explicit_cfg=None):
#     arion_cfg    = arionconfig()
#     election_cfg = draw(electionconfig())
#     votes_cfg    = draw(contestsconfig())
#     attack_cfg   = draw(attackconfig(explicit_cfg=explicit_cfg))
#     cfg = RunConfig(
#         arion_cfg=arion_cfg,
#         election_cfg=election_cfg,
#         votes_cfg=votes_cfg,
#         attack_cfg=attack_cfg
#     )
#     return cfg

### tests ###
