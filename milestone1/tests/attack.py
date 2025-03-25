#!/usr/bin/env python3

import click
import json
import logging
import subprocess
import time

from click_default_group import DefaultGroup
from dotmap import DotMap
from os import environ
from os.path import join, exists, realpath, basename, dirname, splitext
from typing import Optional, List

import hashlib

from glob import glob
from hypothesis import given, settings, seed, Phase
from hypothesis.strategies import composite, lists, sampled_from
from sys import argv

from config import assert_json_roundtrip, projectconfig, ProjectConfig

# TODO remove, or leave in for debugging?
from hypothesis import note

from election import given_valid_election

# name of an attack function
AttackFnName = str

def rm_submitted_ballot():
    raise NotImplementedError

def rm_cast_ballot():
    raise NotImplementedError

def rm_spoiled_ballot():
    raise NotImplementedError

ATTACK_FUNCTIONS = [
    rm_submitted_ballot,
    rm_cast_ballot,
    rm_spoiled_ballot,
]

class AttackConfig(list):
    def __init__(self, attacks: List[AttackFnName]):
        super(AttackConfig, self).__init__()
        for fn_name in attacks:
            self.append(fn_name)

@composite
def attackconfig(draw):
    fns = draw(lists(
        sampled_from(ATTACK_FUNCTIONS),
        min_size=1,
        max_size=1 # TODO how many would be useful? at least 3-4 right?
    ))
    names = [f.__name__ for f in fns]
    cfg = AttackConfig(attacks=names)
    return cfg

@given(cfg=attackconfig())
@settings(max_examples=1_000)
def test_roundtrip_attackcfg(cfg: AttackConfig):
    assert_json_roundtrip(cfg)

# like given_valid_election, but also generates and applies an arbitrary attack
# TODO can it be written in terms of given_valid_election rather than separately?
def given_attacked_election():
    return yad([
        seed(get_random_seed()),
        settings(
            # derandomize=True, # this is already default?
            max_examples=2,
            deadline=None,
            phases=(Phase.explicit, Phase.reuse, Phase.generate),
        ),
        given(cfg=projectconfig(), attack=attackconfig()),
        prerun_test_election, # TODO prerun_attack too, but how?
    ])

# This almost works, but doesn't allow setting max_examples per given
@given(pcfg=projectconfig(), acfg=attackconfig())
@settings(max_examples=10)
def test_combined_givens(pcfg: ProjectConfig, acfg: AttackConfig):
    note(pcfg)
    note(acfg)
    assert True
