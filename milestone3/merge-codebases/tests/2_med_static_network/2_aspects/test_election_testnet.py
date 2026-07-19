import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_init_tx(init_tx: Transaction):
    # This is mainly for testing that the teardown works.
    # TODO is there a better way to do that explicitly?
    assert isinstance(init_tx, Transaction)

def test_election_config(election_cfg: ElectionConfig):
    assert isinstance(election_cfg, ElectionConfig)

def test_election_context(election_ctx: ElectionContext):
    assert isinstance(election_ctx, ElectionContext)
