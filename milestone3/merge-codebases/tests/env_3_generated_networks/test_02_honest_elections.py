# TODO import from runconfig.py


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
        attack_cfg=[] # only difference
    )
    return cfg



