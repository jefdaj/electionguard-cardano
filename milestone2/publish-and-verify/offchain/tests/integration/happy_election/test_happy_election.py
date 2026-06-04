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
    # admin_tx0 is just the init_tx.
    # We re-export it here to avoid any confusion.
    return init_tx

def test_admin_tx0(admin_tx0: Transaction, admin: Admin):
    LOG.debug(f'admin_tx0: {admin_tx0}')
    assert isinstance(admin_tx0, Transaction)

    # TODO test that the init_tx went through according to the admin subscriber

    assert admin.subscriber.phase() == ElectionConfigPhase(phase=ConfigAnnouncePhase())


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
