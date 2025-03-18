class ArionConfig(dict):
    def __init__(self):
        super(ArionConfig, self).__init__()
        self['project_name'] = 'test'
        self['bind_mounts'] = {
            "scripts": "/scripts",
            "public": "/data/public",
            "private": "/data/private"
        }

class VoteConfig(dict):
    def __init__(self, n_cast: int, n_spoil: int):
        assert n_cast  >= 0
        assert n_spoil >= 0
        self['cast' ] = n_cast
        self['spoil'] = n_spoil

class VotesConfig(dict):
    def __init__(self):
        super(VotesConfig, self).__init__()
        self["Yes"   ] = VoteConfig(3, 1)
        self["No"    ] = VoteConfig(2, 2)
        self["Unsure"] = VoteConfig(1, 3)

class GuardiansConfig(dict):
    def __init__(self, count: int = 3, quorum: int = 2):
        super(GuardiansConfig, self).__init__()
        assert quorum > 0
        assert quorum <= count
        self['count' ] = count
        self['quorum'] = quorum

class DevicesConfig(dict):
    def __init__(self, count: int = 4):
        super(DevicesConfig, self).__init__()
        assert count >= 1
        self['count'] = count

class VerifiersConfig(dict):
    def __init__(self, count: int = 2):
        super(VerifiersConfig, self).__init__()
        self['count'] = count

class ElectionConfig(dict):
    def __init__(self,
        guardians_count  : int = 3,
        guardians_quorum : int = 2,
        devices_count    : int = 3,
        verifiers_count  : int = 2,
    ):
        super(ElectionConfig, self).__init__()
        self['guardians'] : GuardiansConfig(guardians_count, guardians_quorum)
        self['devices'  ] : DevicesConfig(devices_count)
        self['verifiers'] : VerifiersConfig(verifiers_count)

class MainConfig(dict):
    def __init__(self):
        super(MainConfig, self).__init__()
        self['arion'   ] = ArionConfig()
        self['election'] = ElectionConfig()
        self['votes'   ] = VotesConfig()
