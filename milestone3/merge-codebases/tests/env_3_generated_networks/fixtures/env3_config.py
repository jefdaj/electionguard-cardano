#!/usr/bin/env python3

# TODO depend on cwd and write the json file there
# TODO factor out honest + attack election test_ files.
# TODO start with those commented ^ and only focus on testing the network up + down harness

from hypothesis import assume
from hypothesis.strategies import integers, composite


### config classes ###

class BindMountsJson(dict):
    def __init__(self):
        super(BindMountsConfig, self).__init__()
        self["scripts"] = "/scripts"
        # self["mockchain"] = "/data/mockchain"
        self["private"] = "/data/private"
        # TODO qrcodes

class ArionJson(dict):
    def __init__(self):
        super(ArionConfig, self).__init__()
        self['project_name'] = 'test' # TODO change?
        self['data_dir'] = 'data' # TODO change?
        self['bind_mounts'] = BindMountsJson()

class VoteJson(dict):
    def __init__(self, n_cast: int, n_spoil: int):
        super(VoteConfig, self).__init__()
        assert n_cast  >= 0
        assert n_spoil >= 0
        self['cast' ] = n_cast
        self['spoil'] = n_spoil

class ContestJson(dict):
    "One contest in the list under `votes`"
    # TODO less confusing names
    def __init__(self, question: str, answers: Dict[str, VoteConfig]):
        super(ContestConfig, self).__init__()
        self['question'] = question
        self['answers' ] = answers

class GuardiansJson(dict):
    def __init__(self, count: int = 3, quorum: int = 2):
        super(GuardiansConfig, self).__init__()
        assert quorum > 0 # TODO require at least 2 for realistic use?
        assert quorum <= count
        self['count' ] = count
        self['quorum'] = quorum

class DevicesJson(dict):
    def __init__(self, count: int = 4):
        super(DevicesConfig, self).__init__()
        assert count >= 1
        self['count'] = count

class VerifiersJson(dict):
    def __init__(self, count: int = 2):
        super(VerifiersConfig, self).__init__()
        self['count'] = count

class ElectionJson(dict):
    def __init__(self,
        guardians_count  : int = 3,
        guardians_quorum : int = 2,
        devices_count    : int = 3,
        verifiers_count  : int = 2,
    ):
        super(ElectionConfig, self).__init__()
        self['guardians'] = GuardiansJson(guardians_count, guardians_quorum)
        self['devices'  ] = DevicesJson(devices_count)
        self['verifiers'] = VerifiersJson(verifiers_count)

class RunJson(dict):
    def __init__(self, arion_cfg, election_cfg, votes_cfg, attack_cfg):
        super(RunConfig, self).__init__()
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
