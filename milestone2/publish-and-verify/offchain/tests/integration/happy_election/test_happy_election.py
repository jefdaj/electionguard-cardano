import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture
import logging
import time

LOG = logging.getLogger(__name__)


### admin_tx0 ###

@per_election_fixture
def admin_tx0(init_tx: Transaction) -> Transaction:
    # admin_tx0 is just the init_tx renamed for clarity.
    return init_tx

def assert_admin_tx0_indexed(sub: ElectionSubscriber):
    history = sub.history
    states  = sub.states
    utxos   = sub.utxos
    seen    = sub._seen_tx_ids
    last    = sub._last_tx_key
    phase   = sub.phase()

    for sub_map in [history, states, utxos]:
        assert ADMIN_CHANNEL_ID in sub_map
        assert len(sub_map) == 1

    assert states[ADMIN_CHANNEL_ID].state.seq == 0
    assert len(history[ADMIN_CHANNEL_ID]) == 1
    assert last is not None
    assert len(seen) == 1
    assert phase == ElectionConfigPhase(phase=ConfigAnnouncePhase())

def test_admin_tx0(admin_tx0: Transaction, funder: Funder, admin: Admin):
    LOG.debug(f'admin_tx0: {admin_tx0}')
    assert isinstance(admin_tx0, Transaction)

    # both (all) nodes should agree on the current election state
    # TODO generalize this
    assert_admin_tx0_indexed(funder.subscriber)
    assert_admin_tx0_indexed(admin.subscriber)

### admin_tx1 ###

@per_election_fixture
def admin_tx1(
        admin: Admin,
        admin_tx0: Transaction,
    ) -> Transaction:
    raise NotImplementedError

# def test_admin_tx1(admin_tx1: Transaction):
#     LOG.debug(f'admin_tx1: {admin_tx1}')
#     assert isinstance(admin_tx1, Transaction)
#     # TODO write phase tracking for the admin subscriber
#     # TODO test that the admin subscriber has picked up the phase change
#     # assert admin.phase() == ...
