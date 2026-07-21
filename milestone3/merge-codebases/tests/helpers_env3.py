from hypothesis import given, settings, seed, Phase
import pytest
from sys import argv
import os

def get_random_seed():
    """Random seed can be set per dev session, which offers a good
    balance between caching and making sure different values work.
    This is the top level main seed. It controls which random configs
    hypothesis generates, and the hashes of the configs control the
    downstream attack random seeds."""
    try:
        seed: int = int(os.environ['EGC_RANDOM_SEED'])
    except KeyError:
        seed = 1234
    return seed

# "yet another decorator"
# https://stackoverflow.com/a/4122845
def yad(decorators):
    def decorator(f):
        for d in reversed(decorators):
            f = d(f)
        return f
    return decorator

# A somewhat mind bending hack to make hypothesis reuse cached test elections.
# This way we can define a lot of rapid tests that make individual assertions
# about the results. It's kind of like a hybrid between givens and pytest
# fixtures: we generate the election configs randomly, but then reuse the same
# random values across lots of tests.
#
# Notes:
# - prerun_test_election is a separate idea that was also convenient to tack on here
# - max_examples really is a max; hypothesis will often run fewer
#
# TODO is this a partial solution to https://github.com/HypothesisWorks/hypothesis/issues/114
# TODO top level CLI arg for max_examples here?
# TODO if no args needed, remove this def lambda
def given_election(max_examples: int, attack_cfg_fn=lambda: {}):
    return yad([
        seed(get_random_seed()),
        settings(
            derandomize  = False,
            max_examples = max_examples,
            deadline     = None,
            phases       = (Phase.explicit, Phase.reuse, Phase.generate),
        ),
        given(cfg=attack_cfg_fn()),
        prerun_test_election,
    ])

def assert_json_roundtrip(cfg):
    tmp  = json.dumps(cfg)
    cfg2 = json.loads(tmp)
    assert cfg == cfg2


