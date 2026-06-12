# Test order roughly matches onchain/tests/integration/happy_subchannel.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from test_utils import per_election_fixture, assert_nodes_in_sync
import logging
import time

LOG = logging.getLogger(__name__)


## ----------- nodes -----------

# TODO factor out fixtures?

@per_election_fixture
def guardian1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian1_wallet: {w}')
    return w

@per_election_fixture
def guardian1(
        election: ElectionContext,
        guardian1_wallet: Wallet
    ) -> GuardianNode:
    node = GuardianNode(
        election   = election,
        wallet     = guardian1_wallet,
        role_index = 1,
    )
    LOG.debug(f'guardian1: {node}')
    try:
        yield node
    finally:
        node.stop()


## ----------- setup for adding single subchannel -------------

# TODO factor out fixtures?

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

@pytest.mark.testnet
def test_admin_tx0(
        admin: AdminNode,
        admin_s0: ChannelState,
        admin_tx0: Transaction,
    ):
    LOG.debug(f'admin_tx0: {admin_tx0}')
    assert isinstance(admin_tx0, Transaction)

    # admin state should match admin_s0
    # we could use funder.subscriber here; they should match
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s0

@pytest.mark.testnet
def test_admin_tx0_sub(
        funder: FunderNode,
        admin: AdminNode,
        admin_tx0: Transaction,
    ):
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)

@per_election_fixture
def admin_s1(
        admin_s0: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = admin_s0.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][1][1],
        phase       = static_phases[1],
        seq         = 1,
    ))

@per_election_fixture
def admin_tx1(
        admin: AdminNode,
        admin_tx0: Transaction,
        static_transactions,
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][1][1],
        new_phase   = static_phases[1],
    )
    LOG.debug(f'admin_tx1: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx1(
        admin: AdminNode,
        admin_s1: ChannelState,
        admin_tx1: Transaction,
    ):
    assert isinstance(admin_tx1, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s1

@pytest.mark.testnet
def test_admin_tx1_sub(
        funder: FunderNode,
        admin: AdminNode,
        admin_tx1: Transaction,
    ):
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)


## -------- alternate admin_tx2: add single subchannel --------

# @per_election_fixture
# def add_action(subchannel_id: ChannelId) -> ElectionAction:
#     return AddSubChannels(channels=[subchannel_id])

@per_election_fixture
def single_onboarding_info(
        guardian1: GuardianNode,
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        guardian1.channel_id() : guardian1.publisher.wallet.vkh
    }
    return info

@per_election_fixture
def single_nodes(
        funder: FunderNode,
        admin: AdminNode,
        guardian1: GuardianNode,
    ) -> list[ElectionNode]:
        return [admin, guardian1]

@per_election_fixture
def admin_s2(
        admin_s1: ChannelState,
        single_onboarding_info: dict[ChannelId, VerificationKeyHash],
        static_phases,
    ) -> ChannelState:
    prev = admin_s1.state
    return AdminChannel(state=replace(
        prev,
        subchannels = [k for k in single_onboarding_info.keys()],
        new_records = [],
        phase       = static_phases[2],
        seq         = 2, # does matter now
    ))

@per_election_fixture
def single_add_tx(
        admin: AdminNode,
        admin_tx1: Transaction,
        single_onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    ch_strs = [channel_id_to_string(k) for k in single_onboarding_info.keys()]
    LOG.info(f'admin got onboarding info from {', '.join(ch_strs)}')
    tx = admin.add_subchannels(
        subchannels = single_onboarding_info,
        subchannel_ada = 10,
        done_onboarding = True, # TODO remove?
    )
    LOG.debug(f'single_add_tx: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_single_add_tx(
        admin: AdminNode,
        single_nodes: list[ElectionNode],
        single_add_tx: Transaction,
        single_admin_s3: ChannelState,
    ):
    assert isinstance(single_add_tx, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == single_admin_s3, 'admin unexpected state'
    assert_nodes_in_sync(single_nodes)
