import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture, assert_subscribers_in_sync
from static_records import STATIC_PHASES, STATIC_TRANSACTIONS
import logging
import time

LOG = logging.getLogger(__name__)

# shorthand
SUBCHANNEL_IDS = STATIC_TRANSACTIONS['admin'][2][0].channels
[G1, G2, G3, D1, V1] = SUBCHANNEL_IDS


### admin_tx0 ###

@per_election_fixture
def admin_s0(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = [],
        new_records = [],
        phase       = ElectionConfigPhase(ConfigAnnouncePhase()),
        seq         = 0,
    ))

@per_election_fixture
def admin_tx0(init_tx: Transaction) -> Transaction:
    # admin_tx0 is just the init_tx renamed for clarity.
    return init_tx

def test_admin_tx0(
        admin_s0: ChannelState,
        admin_tx0: Transaction,
        funder: FunderNode,
        admin: AdminNode,
    ):
    LOG.debug(f'admin_tx0: {admin_tx0}')
    assert isinstance(admin_tx0, Transaction)

    # admin state should match admin_s0
    # we could use funder.subscriber here; they should match
    (_, state) = admin.subscriber.states[ADMIN_CHANNEL_ID]
    assert state == admin_s0

# ... in fact, all nodes should agree on the current state
def test_admin_tx0_sub(
        admin_tx0: Transaction,
        funder: FunderNode,
        admin: AdminNode,
    ):
    assert_subscribers_in_sync([funder, admin])


### admin_tx1 ###

@per_election_fixture
def admin_s1(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = [],
        new_records = STATIC_TRANSACTIONS['admin'][1][1],
        phase       = STATIC_PHASES[1],
        seq         = 1,
    ))

@per_election_fixture
def admin_tx1(admin_tx0: Transaction, admin: AdminNode) -> Transaction:
    phase = STATIC_PHASES[1]
    (_, records) = STATIC_TRANSACTIONS['admin'][1]
    tx = admin.post_public_records(new_records=records, new_phase=phase)
    LOG.debug(f'admin_tx1: {tx}')
    admin.publisher.wait_for_confirmation(tx)
    return tx

def test_admin_tx1(
        admin: AdminNode,
        admin_s1: ChannelState,
        admin_tx1: Transaction,
    ):
    assert isinstance(admin_tx1, Transaction)
    (_, state) = admin.subscriber.states[ADMIN_CHANNEL_ID]
    assert state == admin_s1

def test_admin_tx1_sub(
        admin_tx1: Transaction,
        funder: FunderNode,
        admin: AdminNode,
    ):
    assert_subscribers_in_sync([funder, admin])


### admin_tx2 ###

@per_election_fixture
def admin_s2(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = SUBCHANNEL_IDS,
        new_records = [],
        phase       = STATIC_PHASES[2],
        seq         = 2,
    ))

# all the subchannels also have this one as their state0
# aliases for clarity:
g1_s0 = admin_s2
g2_s0 = admin_s2
g3_s0 = admin_s2
d1_s0 = admin_s2
v1_s0 = admin_s2
