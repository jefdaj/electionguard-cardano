import pytest
from typing import List
from egc import *
import logging

LOG = logging.getLogger(__name__)

# Aliases for convenience and documentation.
# In our tests, the convention is that each package tests/integration/<package>
# is a particular usage path through the contract. Most fixtures are package
# scoped.
global_fixture       = pytest.fixture(scope='session')
per_election_fixture = pytest.fixture(scope='package')

def assert_subscribers_in_sync(nodes: List[ElectionNode]):
    if len(nodes) < 2:
        LOG.warning('assert_subscribers_in_sync called with < 2 nodes')
        return
    # one node to compare the others against
    ref = nodes[0]; nodes = nodes[1:]
    for node in nodes:
        assert node.election_phase()   == ref.election_phase()  , "phase mismatch"
        assert node.subscriber.history == ref.subscriber.history, "history mismatch"
        assert node.subscriber.states  == ref.subscriber.states , "state mismatch"
        # assert node.subscriber.utxos   == ref.subscriber.utxos  , "utxos mismatch"
