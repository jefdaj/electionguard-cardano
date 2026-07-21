import pytest
from sys import argv
import os

from hypothesis import assume, given, settings, seed, Phase
from hypothesis.strategies import integers, composite

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
# def given_election(max_examples: int, attack_cfg_fn=lambda: {}):
def given_env3_tmpdir(max_examples: int, attack_cfg_fn=lambda: {}):
    return yad([
        seed(get_random_seed()),
        settings(
            derandomize  = False,
            max_examples = max_examples,
            deadline     = None,
            phases       = (Phase.explicit, Phase.reuse, Phase.generate),
        ),
        given(cfg=attack_cfg_fn()),
        # prerun_test_election,
        setup_env3_tmpdir,
    ])

def assert_json_roundtrip(cfg):
    tmp  = json.dumps(cfg)
    cfg2 = json.loads(tmp)
    assert cfg == cfg2

# TODO depend on cwd and write the json file there
# TODO factor out honest + attack election test_ files.
# TODO start with those commented ^ and only focus on testing the network up + down harness


### config classes ###

class BindMountsJson(dict):
    def __init__(self):
        super(BindMountsJson, self).__init__()
        self["scripts"] = "/scripts"
        # self["mockchain"] = "/data/mockchain"
        self["private"] = "/data/private"
        # TODO qrcodes

class ArionJson(dict):
    def __init__(self):
        super(ArionJson, self).__init__()
        self['project_name'] = 'test' # TODO change?
        self['data_dir'] = 'data' # TODO change?
        self['bind_mounts'] = BindMountsJson()

class VoteJson(dict):
    def __init__(self, n_cast: int, n_spoil: int):
        super(VoteJson, self).__init__()
        assert n_cast  >= 0
        assert n_spoil >= 0
        self['cast' ] = n_cast
        self['spoil'] = n_spoil

class ContestJson(dict):
    "One contest in the list under `votes`"
    # TODO less confusing names
    def __init__(self, question: str, answers: dict[str, VoteJson]):
        super(ContestJson, self).__init__()
        self['question'] = question
        self['answers' ] = answers

class GuardiansJson(dict):
    def __init__(self, count: int = 3, quorum: int = 2):
        super(GuardiansJson, self).__init__()
        assert quorum > 0 # TODO require at least 2 for realistic use?
        assert quorum <= count
        self['count' ] = count
        self['quorum'] = quorum

class DevicesJson(dict):
    def __init__(self, count: int = 4):
        super(DevicesJson, self).__init__()
        assert count >= 1
        self['count'] = count

class VerifiersJson(dict):
    def __init__(self, count: int = 2):
        super(VerifiersJson, self).__init__()
        self['count'] = count

class ElectionJson(dict):
    def __init__(self,
        guardians_count  : int = 3,
        guardians_quorum : int = 2,
        devices_count    : int = 3,
        verifiers_count  : int = 2,
    ):
        super(ElectionJson, self).__init__()
        self['guardians'] = GuardiansJson(guardians_count, guardians_quorum)
        self['devices'  ] = DevicesJson(devices_count)
        self['verifiers'] = VerifiersJson(verifiers_count)

class RunJson(dict):
    def __init__(self, arion_cfg, election_cfg, votes_cfg, attack_cfg):
        super(RunJson, self).__init__()
        self['arion'   ] = arion_cfg
        self['election'] = election_cfg
        self['votes'   ] = votes_cfg
        self['attacks' ] = attack_cfg # TODO import from attacks.py?


### arbitrary config generators ###

def arionconfig():
    cfg = ArionJson()
    return cfg

@composite
def voteconfig(draw):
    n_cast  = draw(integers(min_value=0, max_value=20))
    n_spoil = draw(integers(min_value=0, max_value=20))
    return VoteJson(n_cast, n_spoil)

# TODO why is this defined twice? that can't be the best way...
@composite
def contestconfig(draw):
    return ContestJson(
        question = 'Should pineapple be banned on pizza?',
        answers = {
            'Yes'    : draw(voteconfig()),
            'No'     : draw(voteconfig()),
            'Unsure' : draw(voteconfig()),
        },
    )

@composite
def contestsconfig(draw):

    contest1 = draw(contestconfig())
    cfg = [contest1]

    # This isn't technically necessary; we handle zero-vote elections properly
    # now. But they tend to waste a lot of test runs, so we remove them.
    # It would be fine to comment this out and raise max_examples though.
    n_cast = sum(
        sum([
            vcfg['cast']
            for vcfg in contest['answers'].values()
        ])
        for contest in cfg
    )
    n_spoil = sum(
        sum([
            vcfg['spoil']
            for vcfg in contest['answers'].values()
        ])
        for contest in cfg
    )
    assume(n_cast + n_spoil > 0)

    return cfg

@composite
def electionconfig(draw):
    kwargs = {}

    # I haven't figured out what the key ceremony should look like with only one guardian,
    # and it would be a silly way to deploy real elections, so for now the min is 2.
    # There's no real maximum, but the number of messages grows quadratically.
    kwargs['guardians_count' ] = draw(integers(min_value=2, max_value=8))

    # Both 1 and n_guardians are bad settings for quorum,
    # but we leave them here just to make sure nothing breaks.
    # In reality you want >2 and <n_guardians-1.
    kwargs['guardians_quorum'] = draw(integers(min_value=1, max_value=kwargs['guardians_count']))

    # Any nonzero number is reasonable here, but in real deployments you
    # probably want to keep it low enough that each batch of CIDs posted is a
    # relatively large anonymity set. One "device" can service many voting
    # machines.
    # TODO bias the tests towards more to speed up parallel voting?
    kwargs['devices_count'   ] = draw(integers(min_value=1, max_value=8))

    kwargs['verifiers_count' ] = draw(integers(min_value=0, max_value=3))

    n_containers = 3 * (
       kwargs['guardians_count'] +
       kwargs['devices_count'  ] +
       kwargs['verifiers_count'] +
       1 # admin
    )

    # if n_containers >= 50:
    #     print(f'reject n_containers = {n_containers}')
    assume(n_containers < 50) # TODO tune this

    cfg = ElectionJson(**kwargs)
    return cfg

