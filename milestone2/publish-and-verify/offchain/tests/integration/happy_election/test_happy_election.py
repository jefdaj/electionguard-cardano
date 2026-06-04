import pytest
from pycardano import *
from egc import *
import logging
import time

LOG = logging.getLogger(__name__)

def test_happy_admin_tx0(happy_admin_tx0: Transaction, admin: Admin):
    LOG.debug(f'happy_admin_tx0: {happy_admin_tx0}')
    assert isinstance(happy_admin_tx0, Transaction)

    # TODO test that the init_tx went through according to the admin subscriber

    assert admin.subscriber.phase() == ElectionConfigPhase(phase=ConfigAnnouncePhase())

# def test_happy_admin_tx1(happy_admin_tx1: Transaction):
#     LOG.debug(f'happy_admin_tx1: {happy_admin_tx1}')
#     assert isinstance(happy_admin_tx1, Transaction)
#     # TODO write phase tracking for the admin subscriber
#     # TODO test that the admin subscriber has picked up the phase change
#     # assert admin.phase() == ...
