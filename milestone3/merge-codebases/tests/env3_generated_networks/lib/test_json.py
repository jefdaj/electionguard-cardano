from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Mapping
import hashlib, json

# TODO is testjson a valid name?
# TODO think though the name again

@dataclass(frozen=True, slots=True)
class VoteJson:
    n_cast: int
    n_spoil: int

@dataclass(frozen=True, slots=True)
class ContestJson:
    question: str
    # tuple, not list -> hashable + immutable; ORDER PRESERVED
    answers: tuple[tuple[str, VoteJson], ...]

    def to_json(self) -> dict:
        return {"question": self.question,
                "answers": {k: asdict(v) for k, v in self.answers}}

@dataclass(frozen=True, slots=True)
class GuardiansJson:
    count: int = 3
    quorum: int = 2

    def __post_init__(self):
        assert 0 < self.quorum <= self.count

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
