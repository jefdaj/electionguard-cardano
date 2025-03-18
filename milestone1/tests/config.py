from dataclasses import dataclass, field
from typing import Dict
import json

# @dataclass(frozen=True)
# class ArionConfig:
#     project_name: str = 'test'
#     bind_mounts: Dict[str, str] = field(default={
#         "scripts": "/scripts",
#         "public": "/data/public",
#         "private": "/data/private"
#     })
# 
# @dataclass(frozen=True)
# class GuardiansConfig:
#     count: int
#     quorum: int
# 
# @dataclass(frozen=True)
# class DevicesConfig:
#     count: int
# 
# @dataclass(frozen=True)
# class VerifiersConfig:
#     count: int
# 
# @dataclass(frozen=True)
# class VotesConfig:
#     votes: Dict[str, Dict[str, int]] = field(default={
#         "Yes":    {"cast": 3, "spoil":1},
#         "No":     {"cast": 2, "spoil":2},
#         "Unsure": {"cast": 1, "spoil":3}
#     })
# 
# @dataclass(frozen=True)
# class ElectionConfig:
#     guardians: GuardiansConfig
#     devices: DevicesConfig
#     verifiers: VerifiersConfig
#     question: str = field(default="Are pineapples cool?")

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
        self['cast'] = n_cast
        self['spoil'] = n_spoil

class VotesConfig(dict):
    def __init__(self):
        super(VotesConfig, self).__init__()
        self["Yes"   ] = VoteConfig(3, 1)
        self["No"    ] = VoteConfig(2, 2)
        self["Unsure"] = VoteConfig(1, 3)

class GuardiansConfig(dict):
    def __init__(self, count: int, quorum: int):
        super(GuardiansConfig, self).__init__()
        self['count'] = count
        self['quorum'] = quorum

class DevicesConfig(dict):
    def __init__(self, count: int):
        super(DevicesConfig, self).__init__()
        self['count'] = count

class VerifiersConfig(dict):
    def __init__(self, count: int):
        super(VerifiersConfig, self).__init__()
        self['count'] = count

@dataclass
class MainConfig(dict):

    guardians_count  : int = field(default=3)
    guardians_quorum : int = field(default=3)
    devices_count    : int = field(default=2)
    verifiers_count  : int = field(default=2)

    def __init__(self, *args, **kwargs):
        super(MainConfig, self).__init__(*args, **kwargs)
        self['arion'] = ArionConfig()
        self['election'] = {
            'guardians' : GuardiansConfig(self.guardians_count, self.guardians_quorum),
            'devices'   : DevicesConfig(self.devices_count),
            'verifiers' : VerifiersConfig(self.verifiers_count),
        }
        self['votes'] = VotesConfig()
